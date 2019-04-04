import time
import board
import busio
import displayio
import digitalio

# Written by Dan Cogliano, DanTheGeek.com

# Store images temporarily onto an SD card or CircuitPython filesystem.
# If using the CircuitPython filesystem (= False), you must create a boot.py
# file to switch between read-only and read-write mode to share it
# with the host operating system.
SDCARD = True

# CircuitPython currently natively supports BMP files, but not JPEG files.
# This PHP program converts and scales JPEG images to BMP images for CircuitPyton
# to use. You need to install it on a LAMP server. Details about this are here: 
# https://danthegeek.com/2019/03/20/display-jpeg-images-from-the-internet-using-the-adafruit-pyportal/
conversionurl = "https://{your site}/jpeg2bmp.php"

# uncomment the site you want to use
jpegurl = "https://thispersondoesnotexist.com/image"
#jpegurl = "https://thiscatdoesnotexist.com/"

if SDCARD:
    import adafruit_sdcard
    import storage
    path = "/sd/" # for SD Card version
else:
    path = "/" # for CircuitPython storage


from digitalio import DigitalInOut
import neopixel
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi import adafruit_esp32spi_wifimanager
from adafruit_button import Button

    
print("PyPortal Ghost Frame")
print("Details at DanTheGeek.com")

imagefile = path + "image.bmp"

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
cs = digitalio.DigitalInOut(board.SD_CS)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

status_light = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)

wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light)

if SDCARD:
    sdcard = adafruit_sdcard.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")

bg_group = displayio.Group(max_size=1)

led = digitalio.DigitalInOut(board.D13)
led.switch_to_output()

while True:
    try:
        print("Getting URL data...", end='')
        response = wifi.get(conversionurl + "?width=320&url="+jpegurl,
            headers={"User-Agent":"Mozilla/5.0",
             "Connection":"Keep-Alive"},
            stream=True)
        print("Got it")
        readsize = 0
        try:
            print("writing to " + imagefile)
            with open(imagefile, "wb") as fp:
                for i in response.iter_content(20*1024):
                    try:
                        if i:
                            fp.write(i);
                            print(".", end='')
                            readsize += len(i)
                    except (ValueError, RuntimeError) as e:
                        print("done")
                        readsize += len(i)
                fp.close()
                response.close()
                print("done writing ", readsize, " bytes")
                imgfile = open(imagefile, "rb")
                background = displayio.OnDiskBitmap(imgfile)
                position = (0, -40)  # default in top corner
                try:
                    bg_sprite = displayio.TileGrid(background,
                        pixel_shader=displayio.ColorConverter(),
                        position=position)
                except TypeError:
                    bg_sprite = displayio.TileGrid(background,
                        pixel_shader=displayio.ColorConverter(),
                        x=position[0], y=position[1])
                while bg_group:
                    bg_group.pop()
                print("displaying image " + imagefile)
                bg_group.append(bg_sprite)
                board.DISPLAY.refresh_soon()
                board.DISPLAY.wait_for_frame()
                board.DISPLAY.show(bg_group)
                print("done")
        except OSError as e:
            print("OS Error ", e)
            delay = 0.5
            if e.args[0] == 28:
                delay = 0.25
            while True:
                led.value = not led.value
                time.sleep(delay)
        except (ValueError, RuntimeError) as e:
            print("Failed writing to file", e)
    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        wifi.reset()
        continue
    time.sleep(0)
