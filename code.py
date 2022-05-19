"""
Eric Sanman
TriMet API Python Proof-of-Concept
19 May 2022

Prints arrivals of two given stopIDs arrival time using TriMet API.
"""
# Import everything needed
import board
import microcontroller
import gc
import busio
from digitalio import DigitalInOut
import adafruit_requests as requests
import time
import adafruit_datetime as datetime
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_bitmap_font import bitmap_font
import displayio
import adafruit_display_text.label
from adafruit_datetime import datetime
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.matrixportal import MatrixPortal

ERROR_RESET_THRESHOLD = 1
UPDATE_DELAY = 15
SYNC_TIME_DELAY = 30
BACKGROUND_IMAGE = 'g-dashboard.bmp'


# === CONNECT Wi-Fi ===
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets not found!")
    raise

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
socket.set_interface(esp)
requests.set_socket(socket, esp)

print("Connecting to AP...")
while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except RuntimeError as e:
        print("could not connect to AP, retrying: ", e)
        continue
print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)

# === DISPLAY SETUP ===
matrix = Matrix()
display = matrix.display

# === DRAWING SETUP ===
group = displayio.Group()
bitmap = displayio.OnDiskBitmap(open(BACKGROUND_IMAGE, 'rb'))
colors = [0x444444, 0xDD8000]  # [dim white, gold]

font = bitmap_font.load_font("fonts/6x10.bdf")
text_lines = [
    displayio.TileGrid(bitmap, pixel_shader=getattr(bitmap, 'pixel_shader', displayio.ColorConverter())),
    adafruit_display_text.label.Label(font, color=colors[0], x=16, y=3, text="PSU>CITY"),
    adafruit_display_text.label.Label(font, color=colors[1], x=16, y=11, text="- mins"),
]
# === MAIN PREFS ===
apiKey = "redacted"
locIDs = [13722]
GET_URL = f"http://developer.trimet.org/ws/v2/arrivals?locIDs={locIDs[0]}&appID={apiKey}&arrivals=1"

# === GET ARRIVAL INFO FROM TRIMET ===
def get_train_arrival_in_mins():
    epochArrival = int(0)
    timeReturn = int(0)
    timeNow = int(0)
    arrivalTimeEpoch = int(0)
    minutesToArrival = int(0)
    print("Fetching JSON data from TriMet!")
    returnData = requests.get(GET_URL)
    jsonData = returnData.json()
    ifDeparted = jsonData['resultSet']['arrival'][0]['departed']

    if ifDeparted == False:
        minutesToArrival = "no train"
        print("The train is sleeping :)\nUpdating display...")
        return minutesToArrival
    else:
        epochArrival = int(jsonData['resultSet']['arrival'][0]['scheduled'])
        stopDesc = str(jsonData['resultSet']['arrival'][0]['shortSign'])
        locDesc = str(jsonData['resultSet']['location'][0]['desc'])

        timeReturn = requests.get("http://worldtimeapi.org/api/timezone/America/Los_Angeles") # fetch time in LA
        timeData = timeReturn.json() # open json
        timeNow = int((timeData['unixtime']) * 1000) # parse json for time and convert to ms
        arrivalTimeEpoch = epochArrival - timeNow

        minutesToArrival = int(arrivalTimeEpoch/(1000*60)%60) # ms to s
        print(f"TimeNow: {timeNow}\nEpochArrival: {arrivalTimeEpoch}\nEpochArrival: {arrivalTimeEpoch}\nMinutesArrival: {minutesToArrival}")
        print("Time calculation complete!\nUpdating display...")
        return minutesToArrival

def update_text(stop0):
    text_lines[2].text = "%s m" % (stop0)
    display.show(group)
    print("Display updated!")

# === MAIN LOOP ===

for x in text_lines:
    group.append(x)
display.show(group)

error_counter = 0
last_time_sync = None
while True:
    try:
        if last_time_sync is None or time.monotonic() > last_time_sync + SYNC_TIME_DELAY:
            last_time_sync = time.monotonic()
        arrivals = get_train_arrival_in_mins()
        update_text(arrivals)
    except (ValueError, RuntimeError) as e:
        print("Some error occured, retrying! -", e)
        error_counter = error_counter + 1
        if error_counter > ERROR_RESET_THRESHOLD:
            microcontroller.reset()

    time.sleep(UPDATE_DELAY)
