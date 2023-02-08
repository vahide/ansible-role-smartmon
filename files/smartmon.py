#/usr/bin/python3
#python script to get smartctl metrics for monitoring disk 
#output the metric to text file for node exporter

import json
import string
import os
import sys
import time



DeviceList = []
SmartAvailable="\n# HELP smartmon_device_smart_available"
SmartEnabled="\n# HELP smartmon_device_smart_enabled"
Temprature="\n# HELP smartmon_temperature_celsius"
RawReadErrorRate="\n# HELP smartmon_raw_read_error_rate"
PowerOnHour="\n# HELP smartmon_power_on_hour"
ReportedUncorrect="\n# HELP smartmon_reported_uncorrect"
CurrentPendingSector="\n# HELP smartmon_current_pending_sector"
CommandTimeout="\n# HELP smartmon_Command_Timeout"
RealoocatedSectorsCount="\n# HELP smartmon_reallocated_sectors_count"
ReadErrors="\n# HELP smartmon_read_errors"
WriteError="\n# HELP smartmon_write_error"
ScsiGrownDefectList="\n# HELP smartmon_scsi_grown_defect_list"
Health="\n# HELP smartmon_device_smart_healthy"

BayCount=os.popen('ssacli ctrl slot=0 pd all show detail | grep -i bay | wc -l').read()
Disk=os.popen("lsblk | grep ^sd | head -n1 | awk '{print $1;}'").read().rstrip()

def get_bash_metrics():
    global SmartAvailable
    global SmartEnabled

    for i in range(0,int(BayCount)):
        cmd1 = "smartctl -a  -d cciss,{} /dev/{} |  grep -i 'serial number' | sed 's/.*:\s*//'".format(i,Disk)
        SN=os.popen(cmd1).read().rstrip()
        cmd2 = "smartctl -a  -d cciss,{}  -j  /dev/{} > 'smart-{}.json'".format(i,Disk,SN) 
        os.system(cmd2)
        DeviceList.append("smart-{}.json".format(SN))
    
        isAvailable=0
        isEnabled=0
        id="smartctl -a  -d cciss,{} /dev/{}".format(i,Disk)
        cmd4 = id + "  | grep -i 'SMART support is' | awk '$1 == \"SMART\" {print $4}'"
        SmartAvail = os.popen(cmd4).read()
        if (SmartAvail.splitlines()[0]).casefold() == "available":
            if (SmartAvail.splitlines()[1]).casefold() == "enabled":
                isAvailable=1
                isEnabled=1
            elif (SmartAvail.splitlines()[1]).casefold() != "enabled":
                isAvailable=1
                isEnabled=0
        elif (SmartAvail.splitlines()[0]).casefold() != "available":
            isAvailable=0
            isEnabled=0
        SmartAvailable = SmartAvailable + "\n" + "smartmon_device_smart_available{" + 'serial_number="{}"'.format(SN) + "} " +  str(isAvailable) 
        SmartEnabled = SmartEnabled + "\n" + "smartmon_device_smart_enabled{" + 'serial_number="{}"'.format(SN) + "} " +  str(isEnabled)


def get_json_metrics():
    global Health
    global Temprature
    global ReadErrors
    global WriteError
    global ScsiGrownDefectList
    global RawReadErrorRate
    global PowerOnHour
    global ReportedUncorrect
    global CurrentPendingSector
    global CommandTimeout
    global RealoocatedSectorsCount

    for index,device in enumerate(DeviceList):
        with open(device, 'r')  as f:
            data = json.load(f)       
        if "smart_status" in data:
            HelathValue = 0
            if str(data["smart_status"]["passed"]).lower() == "true":
                HealthValue = 1
            else:
                HealthValue = 0
            Health = Health + "\n" + "smartmon_device_smart_healthy{" + 'serial_number="{}"'.format(data["serial_number"]) + "} " + str(HealthValue)
            
    
        if "ata_smart_attributes" in data:
            for item in data["ata_smart_attributes"]["table"]:
                if item["id"] == 194:
                   Temprature = Temprature + "\n" + "smartmon_temperature_celsius{" + 'serial_number="{}"'.format(data["serial_number"]) + "} " + item['raw']["string"][:2]
                if item["id"] == 1:
                   RawReadErrorRate = RawReadErrorRate + "\n" +  "smartmon_raw_read_error_rate{" + 'serial_number="{}"'.format(data["serial_number"]) + "} " + item['raw']["string"]
                if item["id"] == 9:
                   PowerOnHour = PowerOnHour + "\n" + "smartmon_power_on_hour{" + 'serial_number="{}"'.format(data["serial_number"]) + "} " + item['raw']["string"]
                if item["id"] == 187:
                   ReportedUncorrect = ReportedUncorrect + "\n" + "smartmon_reported_uncorrect{" + 'serial_number="{}"'.format(data["serial_number"]) + "} " + item['raw']["string"]
                if item["id"] == 197:
                   CurrentPendingSector = CurrentPendingSector + "\n" + "smartmon_current_pending_sector{" + 'serial_number="{}"'.format(data["serial_number"]) + "} " + item['raw']["string"]
                if item["id"] == 188:
                   CommandTimeout = CommandTimeout + "\n" + "smartmon_command_timeout{" + 'serial_number="{}"'.format(data["serial_number"]) + "} " + item['raw']["string"]
                if item["id"] == 5:
                   RealoocatedSectorsCount = RealoocatedSectorsCount + "\n" + "smartmon_reallocated_sectors_count{" + 'serial_number="{}"'.format(data["serial_number"]) + "} " + item['raw']["string"]
        else:
            index+1
            if "temperature" in data :
                Temprature = Temprature + "\n" + "smartmon_temperature_celsius{" + 'serial_number="{}"'.format(data["serial_number"]) + "} " + str(data["temperature"]["current"])
            else:
                Temprature = Temprature + "\n" + "smartmon_temperature_celsius{" + 'serial_number="{}"'.format(data["serial_number"]) + "} " + "-1"
            if "scsi_error_counter_log" in data :
                ReadErrors = ReadErrors + "\n" + "smartmon_read_errors{" + 'serial_number="{}"'.format(data["serial_number"]) + "} " + str(data["scsi_error_counter_log"]["read"]["total_uncorrected_errors"])
                WriteError = WriteError + "\n" + "smartmon_write_errors{" + 'serial_number="{}"'.format(data["serial_number"]) + "} " + str(data["scsi_error_counter_log"]["write"]["total_uncorrected_errors"])
            else:
                ReadErrors = ReadErrors + "\n" + "smartmon_read_errors{" + 'serial_number="{}"'.format(data["serial_number"]) + "} " + "-1"
                WriteError = WriteError + "\n" + "smartmon_write_errors{" + 'serial_number="{}"'.format(data["serial_number"]) + "} " + "-1"
            if "scsi_grown_defect_list" in data :
                ScsiGrownDefectList = ScsiGrownDefectList + "\n" + "smartmon_scsi_grown_defect_list{" + 'serial_number="{}"'.format(data["serial_number"]) + "} " + str(data["scsi_grown_defect_list"])
            else:
                ScsiGrownDefectList = ScsiGrownDefectList + "\n" + "smartmon_scsi_grown_defect_list{" + 'serial_number="{}"'.format(data["serial_number"]) + "} " + "-1"

def write_file():
    FileName = "/var/lib/node_exporter/smart_metrics.prom"
    result = (Health + SmartEnabled + SmartAvailable + Temprature + ReadErrors + WriteError + ScsiGrownDefectList + RawReadErrorRate + PowerOnHour + ReportedUncorrect + CurrentPendingSector + CommandTimeout + RealoocatedSectorsCount + "\n") 
    f = open( FileName , "w")
    f.write(result)
    f.close()


def remove_json_files():
    for index,device in enumerate(DeviceList):
        os.system("rm {}".format(device))



get_bash_metrics()
get_json_metrics()
write_file()
remove_json_files()

