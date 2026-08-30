import math

import numpy as np
from opendbc.can import CANPacker
from opendbc.car import Bus
from opendbc.car.lateral import apply_steer_angle_limits_vm
from opendbc.car.interfaces import CarControllerBase
from opendbc.car.tesla.teslacan import TeslaCAN
from opendbc.car.tesla.teslacan_legacy import TeslaCANRaven
from opendbc.car.tesla.values import CarControllerParams, CANBUS, LEGACY_CARS, CAR
from opendbc.car.vehicle_model import VehicleModel
from opendbc.sunnypilot.car.tesla.coop_steering import CoopSteeringCarController


def get_safety_CP():
  # We use the TESLA_MODEL_Y platform for lateral limiting to match safety
  # A Model 3 at 40 m/s using the Model Y limits sees a <0.3% difference in max angle (from curvature factor)
  from opendbc.car.tesla.interface import CarInterface
  return CarInterface.get_non_essential_params("TESLA_MODEL_Y")


# Cooperative steering on the LEGACY (HW1) platform.
#
# On newer Teslas coop steering is a control type change (ANGLE_CONTROL -> LANE_KEEP_ASSIST),
# but the legacy safety model rejects any type other than NONE/ANGLE_CONTROL, and treats
# LANE_KEEP_ASSIST as "stock LKAS is driving" -- which blocks our steering entirely.
# So here we convert the driver's torsion bar torque into an angle offset ourselves and add it
# to the requested angle BEFORE the usual rate limiter, so panda's angle checks still apply
# unchanged. Above hands_on_level 3 the EPS drops out on its own, so the useful range is below it.
#
# Tuning comes from 30k engaged samples (2026-08-15 logs): torque is under 0.4 Nm 95% of the
# time with hands resting, and 1.5-2.4 Nm when the driver actually pushes.
#
# Retuned after the first real drive (2026-08-17): the EPS reports hands_on_level 3 at about
# 2.1-2.3 Nm and we dropped out there twice, so the usable band was only 0.6-2.0 Nm and the top
# third of the gain curve was unreachable. Two changes: more offset inside that band, and (below)
# we hold on until level 4 while coop steering is on.
# v2 (2026-08-18): the offset is now expressed as LATERAL ACCELERATION and converted to an angle
# through the vehicle model, so the same push feels the same at 30 and at 120 km/h. The old fixed
# deg/Nm gain gave wildly different results across the speed range.
COOP_TORQUE_DEADBAND = 0.5  # Nm, above the resting noise floor (measured: <0.4 Nm with hands resting)
# Measured from the raw CAN of route 0000015f (2026-08-18): every single dropout was
# EAC_INHIBITED / HANDS_ON at the EPS's own hands_on_level 3, seen from 1.56 Nm upward
# (median 2.67). NOT angle rate, NOT torsion safety. So the usable band ends around 2 Nm and
# asking for full assist above that would put the top of the curve out of reach -- the exact
# problem v1 was retuned for. Hence 2.0, not 2.5.
COOP_TORQUE_MAX = 2.0       # Nm, full assist here
COOP_MAX_LAT_ACCEL = 1.0    # m/s2 at full push (dzid26 uses 2.0 on the 3/Y; we start at half)
COOP_MAX_OFFSET = 15.0      # deg of steering wheel, hard ceiling
COOP_OFFSET_RATE = 0.4      # deg per 25 Hz frame, i.e. 10 deg/s
# The stock cutoff is hands_on_level 3. With coop steering on, that fires exactly when the driver
# is doing what the feature is for, so we hold on one level longer. The EPS still gives up on its
# own above that, which is the real backstop -- this only removes OUR early exit.
COOP_HANDS_ON_LIMIT = 4


class CarController(CarControllerBase, CoopSteeringCarController):
  def __init__(self, dbc_names, CP, CP_SP):
    CarControllerBase.__init__(self, dbc_names, CP, CP_SP)
    CoopSteeringCarController.__init__(self)
    self.apply_angle_last = 0
    self.coop_angle_offset = 0.0
    self.packer = CANPacker(dbc_names[Bus.party])
    self.tesla_can = TeslaCAN(CP, self.packer)

    # Vehicle model used for lateral limiting
    self.VM = VehicleModel(get_safety_CP())

    if CP.carFingerprint in LEGACY_CARS:
      if CP.carFingerprint in (CAR.TESLA_MODEL_S_HW1, CAR.TESLA_MODEL_X_HW1,):
        CANBUS.powertrain = CANBUS.party
        CANBUS.autopilot_powertrain = CANBUS.autopilot_party

      self.packers = {CANBUS.party: CANPacker(dbc_names[Bus.party]), CANBUS.powertrain: CANPacker(dbc_names[Bus.pt])}
      self.tesla_can = TeslaCANRaven(self.packers)
      from opendbc.car.tesla.interface import CarInterface
      self.VM = VehicleModel(CarInterface.get_non_essential_params("TESLA_MODEL_S_HW3"))

  def update_legacy_coop_offset(self, CS, lat_active: bool) -> float:
    # See the COOP_* constants above for why HW1 needs its own path. control_type 2 means the
    # TeslaCoopSteering toggle is on; we never send that type on legacy, we only read the flag.
    if not (lat_active and self.coop_steering.control_type == 2):
      self.coop_angle_offset = 0.0
      return 0.0

    torque = CS.out.steeringTorque
    span = COOP_TORQUE_MAX - COOP_TORQUE_DEADBAND
    effort = float(np.clip((abs(torque) - COOP_TORQUE_DEADBAND) / span, 0.0, 1.0))
    if effort <= 0.0:
      target = 0.0
    else:
      # constant lateral acceleration -> curvature -> steering wheel angle, through the vehicle model.
      # Note: this VM carries the STATIC steer ratio (15.0). The value learned on this car is ~13.8
      # (measured 2026-08-18), so the real offset lands ~9% above the nominal target. Harmless for a
      # driver-commanded assist, but it is why the numbers below are a floor, not a promise.
      v = max(CS.out.vEgoRaw, 3.0)
      curv = (effort * COOP_MAX_LAT_ACCEL) / (v * v)
      angle = math.degrees(self.VM.get_steer_from_curvature(curv, v, 0.0))
      target = math.copysign(min(abs(angle), COOP_MAX_OFFSET), torque)

    # Ramp instead of jumping, both when the driver pushes and when they let go.
    self.coop_angle_offset = float(np.clip(target, self.coop_angle_offset - COOP_OFFSET_RATE,
                                           self.coop_angle_offset + COOP_OFFSET_RATE))
    return self.coop_angle_offset

  def update(self, CC, CC_SP, CS, now_nanos):
    CoopSteeringCarController.update(self, self.CP_SP)
    actuators = CC.actuators
    can_sends = []

    # Tesla EPS enforces disabling steering on heavy lateral override force.
    # When enabling in a tight curve, we wait until user reduces steering force to start steering.
    # Canceling is done on rising edge and is handled generically with CC.cruiseControl.cancel
    hands_on_limit = 3
    if self.CP.carFingerprint in LEGACY_CARS and self.coop_steering.control_type == 2:
      hands_on_limit = COOP_HANDS_ON_LIMIT
    lat_active = CC.latActive and CS.hands_on_level < hands_on_limit

    if self.frame % 2 == 0:
      steering_angle_deg = actuators.steeringAngleDeg
      if self.CP.carFingerprint in LEGACY_CARS:
        steering_angle_deg += self.update_legacy_coop_offset(CS, lat_active)

      # Angular rate limit based on speed
      self.apply_angle_last = apply_steer_angle_limits_vm(steering_angle_deg, self.apply_angle_last, CS.out.vEgoRaw, CS.out.steeringAngleDeg,
                                                          lat_active, CarControllerParams, self.VM)
      if self.CP.carFingerprint in LEGACY_CARS:
        cntr = (self.frame // 2) % 16
        can_sends.append(self.tesla_can.create_steering_control(cntr, self.apply_angle_last, lat_active))
      else:
        can_sends.append(self.tesla_can.create_steering_control(self.apply_angle_last, lat_active, self.coop_steering.control_type))

    if self.frame % 10 == 0 and self.CP.carFingerprint not in (CAR.TESLA_MODEL_S_HW1, CAR.TESLA_MODEL_X_HW1,):
      cntr = (self.frame // 10) % 16
      can_sends.append(self.tesla_can.create_steering_allowed(cntr))

    # Longitudinal control
    if self.CP.openpilotLongitudinalControl:
      if self.frame % 4 == 0:
        state = 13 if CC.cruiseControl.cancel else 4  # 4=ACC_ON, 13=ACC_CANCEL_GENERIC_SILENT
        accel = float(np.clip(actuators.accel, CarControllerParams.ACCEL_MIN, CarControllerParams.ACCEL_MAX))
        cntr = (self.frame // 4) % 8
        if self.CP.carFingerprint in LEGACY_CARS:
          can_sends.append(self.tesla_can.create_longitudinal_command(state, accel, cntr, CS.out.vEgo, CC.longActive, CS.out.gasPressed))
        else:
          can_sends.append(self.tesla_can.create_longitudinal_command(state, accel, cntr, CS.out.vEgo, CC.longActive))

    else:
      # Increment counter so cancel is prioritized even without openpilot longitudinal
      if CC.cruiseControl.cancel:
        cntr = (CS.das_control["DAS_controlCounter"] + 1) % 8
        if self.CP.carFingerprint in LEGACY_CARS:
          can_sends.append(self.tesla_can.create_longitudinal_command(13, 0, cntr, CS.out.vEgo, False, CS.out.gasPressed))
        else:
          can_sends.append(self.tesla_can.create_longitudinal_command(13, 0, cntr, CS.out.vEgo, False))

    # TODO: HUD control
    new_actuators = actuators.as_builder()
    new_actuators.steeringAngleDeg = self.apply_angle_last

    self.frame += 1
    return new_actuators, can_sends
