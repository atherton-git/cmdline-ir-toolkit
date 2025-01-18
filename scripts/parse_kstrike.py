#!/usr/bin/env python3
'''
Note: This is a modified version of KScript version 20210624 (https://github.com/brimorlabs/KStrike/tree/master).

Initially Developed January 30, 2021

Updates
2021-06-24 - Added Python3 support
2021-04-26 - Added two new GUIDs to lookup table
2021-02-23 - Built in logic to identify multi-year entries (abnormal, but it can happen)
2021-02-13 - Processed DNS table (if available) and correlates hostname(s) to IPv4 addresses
2024-01-09 - Made small changes to line 251 and 276, changing from "(value > 0)" to "(value is not None)". Added Active Directory Lightweight Directory Service GUID 

DISCLAIMER: 

Copyright (c) 2021-2024, BriMor Labs
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the BriMor Labs nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.


THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL BRIMOR LABS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


Many thanks to:
- Patrick Bennett
- Kevin Stokes
- Mark McKinnon and Mark Baggett (for their work on SRUM parsing scripts which helped with ESE database/field structure
- Microsoft reference material on this artifact: https://docs.microsoft.com/en-us/windows-server/administration/user-access-logging/manage-user-access-logging
'''

import os
import sys
import time
import re
import math
import uuid
import binascii
import struct
import socket
import textwrap
from datetime import timedelta, datetime
import pyesedb

# We import from a sibling file in the same directory
from common_paths import get_toolkit_dirs

# -------------------------------------------------------------------------------------------
# GLOBAL VARIABLES & DICTIONARIES (based on your original script)
# -------------------------------------------------------------------------------------------
kstrikeversionnumber = "20210624"  # KStrike version
StartTime = time.time()            # Record script start time

insertdatefourofyear = []
insertdateyyyymmdd = []
lastaccessfourofyear = []
lastaccessyyyymmdd = []
insertdatehour = []
insertdateday = []
clienttablenumber = None
dnstablenumber = None
totalcountofaccesses = []
badyeardetector = []
correlatedtwoaccessmismatchyear = "No"

Column_Dict = {
    0:'NULL', 1:'Text', 2:'Integer', 3:'Integer', 4:'Integer', 5:'Integer',
    6:'Real', 7:'Real', 8:'Text', 9:'Blob', 10:'Text', 11:'Blob', 12:'Text',
    13:'Integer', 14:'Integer', 15:'Integer', 16:'Text', 17:'Integer'
}

Table_Dict = {
    'MSysObjects':'MSysObjects', 
    'MSysObjectsShadow':'MSysObjectsShadow', 
    'MSysObjids':'MSysObjids', 
    'MSysLocales':'MSysLocales',
    'CLIENTS':'CLIENTS',
    'ROLE_ACCESS':'ROLE_ACCESS',
    'VIRTUALMACHINES':'VIRTUALMACHINES',
    'DNS':'DNS'
}

GUID_Dict = {
    '{10A9226F-50EE-49D8-A393-9A501D47CE04}':'File Server',
    '{4116A14D-3840-4F42-A67F-F2F9FF46EB4C}':'Windows Deployment Services',
    '{48EED6B2-9CDC-4358-B5A5-8DEA3B2F3F6A}':'DHCP Server',
    '{7CC4B071-292C-4732-97A1-CF9A7301195D}':'FAX Server',
    '{7FB09BD3-7FE6-435E-8348-7D8AEFB6CEA3}':'Print and Document Services',
    '{910CBAF9-B612-4782-A21F-F7C75105434A}':'BranchCache',
    '{952285D9-EDB7-4B6B-9D85-0C09E3DA0BBD}':'Remote Access',
    '{B4CDD739-089C-417E-878D-855F90081BE7}':'Active Directory Rights Management Service',
    '{BBD85B29-9DCC-4FD9-865D-3846DCBA75C7}':'Network Policy and Access Services',
    '{C23F1C6A-30A8-41B6-BBF7-F266563DFCD6}':'FTP Server',
    '{C50FCC83-BC8D-4DF5-8A3D-89D7F80F074B}':'Active Directory Certificate Services',
    '{D6256CF7-98FB-4EB4-AA18-303F1DA1F770}':'Web Server',
    '{D8DC1C8E-EA13-49CE-9A68-C9DCA8DB8B33}':'Windows Server Update Services',
    '{AD495FC3-0EAA-413D-BA7D-8B13FA7EC598}':'Active Directory Domain Services',
    '{BD7F7C0D-7C36-4721-AFA8-0BA700E26D9E}':'SQL Server Database Engine',
    '{DDE30B98-449E-4B93-84A6-EA86AF0B19FE}':'MSMQ',
    '{1479A8C1-9808-411E-9739-2D3C5923E86A}':'Windows Server 2016 DatacenterRemote Desktop Gateway',
    '{90E64AFA-70DB-4FEF-878B-7EB8C868F091}':'Windows ServerRemote Desktop Services',
    '{2414BC1B-1572-4CD9-9CA5-65166D8DEF3D}':'SQL Server Analysis Services',
    '{8CC0AC85-40F7-4886-9DAB-021519800418}':'Reporting Services',
    '{4AD13311-EC3B-447E-9056-14EDE9FA7052}':'Active Directory Lightweight Directory Services'
}

DNS_Dict = {}

# These will be updated as we parse columns
Column_Name = ""
Table_name = ""

# -------------------------------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------------------------------

def win_date_bin_to_datetime(win_date_bin):
    """Converts the datetime field of the CLIENTS table specifically (Windows FILETIME)."""
    global insertdatefourofyear, insertdateyyyymmdd
    global lastaccessfourofyear, lastaccessyyyymmdd
    global insertdatehour, insertdateday
    global Column_Name

    decimaldate = int(struct.unpack("<Q", win_date_bin)[0])
    try:
        windowsdt = datetime(1601,1,1,0,0,0) + timedelta(microseconds=decimaldate/10)
    except:
        windowsdt = "UNRECOGNIZED TIMESTAMP"
    sys.stdout.write(str(windowsdt) + "||")

    fourofyear = str(windowsdt)[0:4]
    fullyyyymmdd = str(windowsdt)[0:10]
    twoofhour = str(windowsdt)[11:13]
    twoofdate = str(windowsdt)[8:10]

    if (len(fourofyear) == 4 and Column_Name == "InsertDate"):
        insertdatefourofyear = fourofyear
        insertdateyyyymmdd = fullyyyymmdd
        insertdatehour = twoofhour
        insertdateday = twoofdate
    elif (len(fourofyear) == 4 and Column_Name == "LastAccess"):
        lastaccessfourofyear = fourofyear
        lastaccessyyyymmdd = fullyyyymmdd

def Check_Column_Type(Table_Record, Column_Type, Column_Number, Record_List, Table_name):
    """
    Reads column data based on type and prints/appends the results to Record_List or stdout.
    This is the original KStrike logic for enumerating DNS and CLIENTS columns.
    """
    global DNS_Dict, Column_Name
    global totalcountofaccesses
    global correlatedtwoaccessmismatchyear, badyeardetector
    global insertdatefourofyear, lastaccessfourofyear
    global insertdateyyyymmdd, lastaccessyyyymmdd
    global insertdatehour, insertdateday

    if Column_Type == 0:
       return
    elif Column_Type in [2,3,4,5]:  # Some integer variant
       val = Table_Record.get_value_data_as_integer(Column_Number)
       return Record_List.append(val)
    elif Column_Type in [6,7]:      # Real / Double
       val = Table_Record.get_value_data_as_floating_point(Column_Number)
       return Record_List.append(val)
    elif Column_Type == 1:          # Boolean => text
       val = Table_Record.get_value_data(Column_Number)
       if val is None:
           return Record_List.append('NULL')
       else:
           return Record_List.append(str(val.decode('utf-16', 'ignore')))
    elif Column_Type == 8:          # DATETIME
       val = Table_Record.get_value_data(Column_Number)
       if val is None:
          return Record_List.append('')
       elif Table_name == "DNS":
          return Record_List.append('')
       else:
          return Record_List.append(win_date_bin_to_datetime(val))
    elif Column_Type == 9:          # BINARY_DATA_TO_HEX (IPv4, IPv6, or MAC checks)
       val = Table_Record.get_value_data(Column_Number)
       if val is None:
          sys.stdout.write("NO BINARY_DATA_TO_HEX||NO BINARY_DATA_TO_HEX||")
       else:
          hexdb = binascii.hexlify(val)
          macaddress = hexdb.decode('utf-8', 'ignore')
          # IP or MAC address checks
          if ((len(hexdb) <= 8) and (Column_Name == "Address")):
              # IPv4 conversion
              if len(hexdb) < 8:
                  hexdb = b'0' + hexdb
              ipaddr = "%i.%i.%i.%i" % (
                  int(hexdb[0:2],16), 
                  int(hexdb[2:4],16), 
                  int(hexdb[4:6],16), 
                  int(hexdb[6:8],16)
              )
              raw_ipaddr_correlations = DNS_Dict.get(ipaddr, "No Match for IP address found")
              ipaddr_correlations = str(raw_ipaddr_correlations).strip("[]")
              sys.stdout.write(macaddress.upper() + "||" + ipaddr + " (" + ipaddr_correlations + ")||")
          elif (((macaddress[:4] == "fe80") or (macaddress[:4] == "2001")) 
                and (Column_Name == "Address") 
                and (len(hexdb) == 32)):
              # IPv6
              colonaddedtohexdb = ':'.join(macaddress[i:i+4] for i in range(0, len(macaddress), 4))
              ipv6Parts = colonaddedtohexdb.split(":")
              macParts = []
              for ipv6Part in ipv6Parts[-4:]:
                  while len(ipv6Part) < 4:
                      ipv6Part = "0" + ipv6Part
                  macParts.append(ipv6Part[:2])
                  macParts.append(ipv6Part[-2:])
              macParts[0] = "%02x" % (int(macParts[0], 16) ^ 2)
              del macParts[4]
              del macParts[3]
              finalmac = ":".join(macParts).upper()
              sys.stdout.write(macaddress.upper() + "||" + colonaddedtohexdb + " IPv6 MAC: " + finalmac + "||")
          elif ((macaddress == "00000000000000000000000000000001")
                and (Column_Name == "Address") 
                and (len(hexdb) == 32)):
              # Localhost IPv6
              sys.stdout.write(macaddress.upper() + "||Local Host ::1||")
          else:
              sys.stdout.write(macaddress.upper() + "||Unable to convert data||")

    elif Column_Type == 10:         # TEXT
       val = Table_Record.get_value_data(Column_Number)
       if val is None:
          return Record_List.append('')
       else:
          return Record_List.append(val.decode('utf-16', 'ignore'))

    elif Column_Type == 11:         # LARGE_BINARY_DATA
       val = Table_Record.get_value_data(Column_Number)
       if val is None:
          return Record_List.append('')
       else:
          return Record_List.append(val)

    elif Column_Type == 12:         # LARGE_TEXT
       val = Table_Record.get_value_data(Column_Number)
       if val is None:
           sys.stdout.write("<BLANK>||")
           return
       else:
           # Possibly DNS IP or hostname
           decoded_val = val.decode('utf-16', 'ignore').replace('\x00', '')
           if (Column_Name == "Address" and Table_name == "DNS"):
               global ip_address_from_dns
               ip_address_from_dns = decoded_val
           elif (Column_Name == "HostName" and Table_name == "DNS"):
               hostname_from_dns = decoded_val
               if ip_address_from_dns in DNS_Dict:
                   DNS_Dict[ip_address_from_dns].append(hostname_from_dns)
               else:
                   DNS_Dict[ip_address_from_dns] = [hostname_from_dns]
           else:
               # Generic large text
               if len(decoded_val) > 1:
                   sys.stdout.write(decoded_val + "||")
               else:
                   sys.stdout.write("<BLANK>||")

    elif Column_Type == 13:         # SUPER_LARGE_VALUE
       val = Table_Record.get_value_data_as_integer(Column_Number)
       return Record_List.append(val)

    elif Column_Type == 14:         # INTEGER_32BIT_UNSIGNED
       val = Table_Record.get_value_data_as_integer(Column_Number)
       if Column_Name == "TotalAccesses":
           totalcountofaccesses = str(val)
           sys.stdout.write(str(val) + "||")
       else:
           sys.stdout.write(str(val) + "||")

    elif Column_Type == 15:         # INTEGER_64BIT_SIGNED
       val = Table_Record.get_value_data_as_integer(Column_Number)
       return Record_List.append(val)

    elif Column_Type == 16:         # GUID
       val = Table_Record.get_value_data(Column_Number)
       if val is None:
           sys.stdout.write("NO GUID DATA||")
       else:
          orgguid = uuid.UUID(bytes_le=val)
          urnguid = orgguid.urn
          rawguid = urnguid[9:].upper()
          fullguid = '{' + rawguid + '}'
          if Column_Name == "RoleGuid":
              GUID_conversion = GUID_Dict.get(fullguid, "No Match for GUID found")
              sys.stdout.write(fullguid + " (" + GUID_conversion + ")||")
          else:
              sys.stdout.write(fullguid + "||")

    elif Column_Type == 17:         # INTEGER_16BIT_UNSIGNED
       val = Table_Record.get_value_data_as_integer(Column_Number)
       if (val is not None) and ("Day" in Column_Name):
           import datetime
           if ((int(insertdatefourofyear) != int(lastaccessfourofyear))
               and (Column_Name != "Day1")
               and (totalcountofaccesses == "2")):
               if correlatedtwoaccessmismatchyear != "Yes":
                   sys.stdout.write(insertdateyyyymmdd + ":1, " + lastaccessyyyymmdd + ":1")
                   correlatedtwoaccessmismatchyear = "Yes"
           else:
               if ((int(insertdatefourofyear) != int(lastaccessfourofyear))
                   and (Column_Name != "Day1")
                   and (totalcountofaccesses > "2")
                   and (badyeardetector != "Yes")):
                   sys.stdout.write("**** WARNING: Multiple years detected, correlated \"DatesAndAccesses\" may not be accurate **** ")
                   badyeardetector = "Yes"
               # Check potential year rollover
               if (Column_Name == "Day1") and (insertdatehour == '23') and (insertdateday == '31'):
                   insertdatefourofyear = str(int(insertdatefourofyear) + 1)
               day_str = Column_Name[3:]
               testingd = datetime.datetime.strptime(f'{day_str} {insertdatefourofyear}', '%j %Y')
               fullconvjd = testingd.strftime("%Y-%m-%d")
               sys.stdout.write(fullconvjd + ": " + str(val) + ", ")
       elif val is not None:
           sys.stdout.write(Column_Name + " " + str(val) + ",")
       else:
           sys.stdout.write("")

def parse_single_esedb(path_to_esedb):
    """
    Parses a SINGLE .mdb file, enumerating DNS and CLIENTS tables
    with the original KStrike logic. Writes to stdout.
    """
    global dnstablenumber, clienttablenumber
    global Column_Name, Table_name
    global StartTime, correlatedtwoaccessmismatchyear, badyeardetector
    global ip_address_from_dns

    # Reset table indices for each new file
    dnstablenumber = None
    clienttablenumber = None

    try:
        file_object = open(path_to_esedb, "rb")
    except Exception as e:
        sys.stderr.write(f"Error opening file {path_to_esedb}: {e}\n")
        return

    esedb_file = pyesedb.file()
    esedb_file.open_file_object(file_object)
    Num_Of_tables = esedb_file.get_number_of_tables()
    sys.stderr.write(f"Parsing '{path_to_esedb}'. Number of tables: {Num_Of_tables}\n")

    # Identify table numbers
    for i in range(Num_Of_tables):
        Table = esedb_file.get_table(i)
        tname = Table.get_name()
        if tname in Table_Dict:
            Table_lookup_name = Table_Dict[tname]
            sys.stderr.write(f"Table {i} = {Table_lookup_name}\n")
            if Table_lookup_name == "DNS":
                dnstablenumber = i
            elif Table_lookup_name == "CLIENTS":
                clienttablenumber = i

    # --- Parse the DNS table ---
    if dnstablenumber is not None:
        DNSTable = esedb_file.get_table(dnstablenumber)
        Table_name = Table_Dict[DNSTable.get_name()]
        Table_Num_Records = DNSTable.get_number_of_records()
        Table_Num_Columns = DNSTable.get_number_of_columns()

        if Table_Num_Records > 0 and Table_name == "DNS":
            for t in range(Table_Num_Records):
                Table_Record = DNSTable.get_record(t)
                for x in range(Table_Num_Columns):
                    Column_Name = Table_Record.get_column_name(x)
                    Column_Type = Table_Record.get_column_type(x)
                    Data_Value = []
                    Check_Column_Type(Table_Record, Column_Type, x, Data_Value, Table_name)
        else:
            sys.stderr.write(f"No DNS records found in '{path_to_esedb}'.\n")
    else:
        sys.stderr.write("No DNS table found.\n")

    # --- Parse the CLIENTS table ---
    if clienttablenumber is not None:
        ClientsTable = esedb_file.get_table(clienttablenumber)
        Table_name = Table_Dict[ClientsTable.get_name()]
        Table_Num_Records = ClientsTable.get_number_of_records()
        Table_Num_Columns = ClientsTable.get_number_of_columns()

        if Table_Num_Records > 0 and Table_name == "CLIENTS":
            # Print the header line
            sys.stdout.write(
                "RoleGuid (RoleName)||TenantId||TotalAccesses||InsertDate||LastAccess||"
                "RawAddress||ConvertedAddress (Correlated_HostName(s))||AuthenticatedUserName||"
                "DatesAndAccesses||\n"
            )

            for t in range(Table_Num_Records):
                Table_Record = ClientsTable.get_record(t)
                badyeardetector = "No"
                correlatedtwoaccessmismatchyear = "No"

                for x in range(Table_Num_Columns):
                    Column_Name = Table_Record.get_column_name(x)
                    Column_Type = Table_Record.get_column_type(x)
                    Data_Value = []
                    Check_Column_Type(Table_Record, Column_Type, x, Data_Value, Table_name)

                sys.stdout.write("||\n")
        else:
            sys.stderr.write(f"No CLIENTS records found in '{path_to_esedb}'.\n")
    else:
        sys.stderr.write("No CLIENTS table found.\n")

    esedb_file.close()

    scriptruntime = time.time() - StartTime
    formattedscriptruntime = int(scriptruntime)
    if formattedscriptruntime > 60:
        import datetime
        totalruntime = str(datetime.timedelta(seconds=int(formattedscriptruntime)))
        sys.stderr.write(f"KStrike processed in {totalruntime} (H:MM:SS)\n")
    else:
        sys.stderr.write(f"KStrike processed in {formattedscriptruntime} seconds\n")

def parse_all_mdb_in_input():
    """
    Loops through all *.mdb files in _input (based on get_toolkit_dirs()),
    and writes the KStrike output to _output/<basename>_kstrike.txt.
    """
    dirs = get_toolkit_dirs()
    input_dir = dirs['input_dir']
    output_dir = dirs['output_dir']

    # Ensure _output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # List all .mdb files in _input
    mdb_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".mdb")]
    if not mdb_files:
        sys.stderr.write(f"No .mdb files found in '{input_dir}'. Nothing to parse.\n")
        return

    for mdb_file in mdb_files:
        full_mdb_path = os.path.join(input_dir, mdb_file)
        base_name, _ = os.path.splitext(mdb_file)
        out_file_path = os.path.join(output_dir, f"{base_name}_kstrike.txt")

        sys.stderr.write(f"\n--- Parsing: {mdb_file} ---\n")
        sys.stderr.write(f"Output => {out_file_path}\n")

        # Redirect stdout to a file for this parse, so user sees the final KStrike output in .txt
        original_stdout = sys.stdout
        try:
            with open(out_file_path, 'w', encoding='utf-8') as out_f:
                sys.stdout = out_f
                parse_single_esedb(full_mdb_path)
        except Exception as e:
            sys.stderr.write(f"Failed parsing {mdb_file}: {e}\n")
        finally:
            sys.stdout = original_stdout

        sys.stderr.write(f"Finished: {mdb_file}\n")

def main():
    # Just parse everything, no user prompts
    parse_all_mdb_in_input()

if __name__ == "__main__":
    main()
