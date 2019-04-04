import board
import digitalio
import storage

# Either of these should work for the PyPortal
switch = digitalio.DigitalInOut(board.D4) # For PyPortal
#switch = digitalio.DigitalInOut(board.D3) # For PyPortal

switch.direction = digitalio.Direction.INPUT
switch.pull = digitalio.Pull.UP

# If the switch pin is connected to ground CircuitPython can write to the drive
# Use a female/female jumper wire to connect the outer pins in the D4 connecter
storage.remount("/", switch.value)
