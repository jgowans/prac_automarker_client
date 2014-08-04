import serial

class InterrigatorInterface:
  def __init__(self):
    self.ser = serial.Serial("/dev/ttyACM0", 115200, timeout=2)
    comms_test() 
  def comms_test(self):
    self.ser.write("PING")
    if self.ser.readline() != "PONG":
      raise("No comms")
  def set_pin(pin):
    pass
  def clear_pin(pin):
    pass
  def write_port(port):
    pass
  def read_pin(pin):
    pass
  def read_port(port):
    pass


