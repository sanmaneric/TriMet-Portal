"""
Eric Sanman
TriMet API Python Proof-of-Concept
26 April 2022

Prints arrivals of up to two given stopIDs arrival time using TriMet API.
"""
# Import everything needed
import requests
import json
import time
import datetime

# === MAIN PREFS ===
url = "http://developer.trimet.org/ws/v2/arrivals"
# MAX 2 locIDs! More will break the program!
locIDs = [13723]
arrivalCount = 1
apiKey = "YOUR-API-KEY"

# === RUN HOURS (24HR FORMAT) ===
startTime = datetime.time(6, 30, 0)
endTime =datetime.time(0, 55, 0)

# === GET ARRIVAL INFO FROM TRIMET ===
def get_train_arrival_in_mins(stopID):
    payload = {'locIDs': stopID,'appID': apiKey,'arrivals': arrivalCount}
    returnData = requests.get(url, params=payload)
    #print(returnData.text)
    
    json_data = json.loads(returnData.text)
    
    epochArrival = json_data['resultSet']['arrival'][0]['scheduled']
    stopDesc = str(json_data['resultSet']['arrival'][0]['shortSign']) 
    locDesc = str(json_data['resultSet']['location'][0]['desc'])
    
    timeNow = int(time.time()) * 1000
    arrivalTimeEpoch = epochArrival - timeNow
    minutesToArrival = (arrivalTimeEpoch/(1000)/60)

    return minutesToArrival, stopDesc, locDesc

# === MAIN LOOP ===

# Replace while true with this to disable while trains are resting
# startTime < datetime.datetime.now() < endTime
while True:
    time.sleep(3 - time.monotonic() % 1) 
    if len(locIDs) == 2:
        minutesToArrival, stopDesc, locDesc = get_train_arrival_in_mins(locIDs[0])
        minutesToArrival1, stopDesc1, locDesc1 = get_train_arrival_in_mins(locIDs[1]) 
        if minutesToArrival > 60:
            print("No trains running.")
            break
        else:
            print(f"{stopDesc} from {locDesc} will arrive in {minutesToArrival:.0f} minutes!")
            print(f"{stopDesc1} from {locDesc1} will arrive in {minutesToArrival1:.0f} minutes!")
            break
    else:
        minutesToArrival, stopDesc, locDesc = get_train_arrival_in_mins(locIDs[0])
        if minutesToArrival > 60:
            print("No trains running.")
            break
        else:
            print(f"{stopDesc} from {locDesc} will arrive in {minutesToArrival:.0f} minutes!")
            break