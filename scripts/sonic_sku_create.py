#! /usr/bin/env python2
"""
usage: sonic_sku_create.py [-h] [-v] [-f FILE | -m MINIGRAPH] [-b BASE] [-r]
                           [-c {new_sku_only,l2_mode_only,new_sku_l2}]
                           [-s SKU] [-p] [-vv]

Create a new SKU

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -f FILE, --file FILE  SKU definition from xml file. -f OR -m must be provided when creating a new SKU
  -m MINIGRAPH, --minigraph MINIGRAPH
                        SKU definition from minigraph file. -f OR -m must be provided when creating a new SKU
  -b BASE, --base BASE  SKU base definition  
  -r, --remove          Remove SKU folder
  -c {new_sku_only,l2_mode_only,new_sku_l2}, --cmd {new_sku_only,l2_mode_only,new_sku_l2}
                        Choose action to preform (Generate a new SKU, Configure L2 mode, Both
  -s SKU, --sku SKU     SKU name to be used when creating a new SKU or for  L2 configuration mode
  -p, --print           Print port_config.ini without creating a new SKU
  -vv, --verbose        Verbose output


"""

from __future__ import print_function

import argparse
import json
import os
import re
import subprocess
import swsssdk
import traceback
import sys
import shutil
import sonic_platform
#import minigraph  

from tabulate import tabulate
import xml.etree.ElementTree as ET
from lxml.etree import QName

minigraph_ns = "Microsoft.Search.Autopilot.Evolution"
minigraph_ns1 = "http://schemas.datacontract.org/2004/07/Microsoft.Search.Autopilot.Evolution"

DEFAULT_DEV_PATH = '/usr/share/sonic/device/'
### port_config.ini header
PORTCONFIG_HEADER = ["# name", "lanes", "speed", "alias", "index"]


class SkuCreate(object):
	"""
	Process aclstat
	"""

	def __init__(self):
		###self.metadata = {}
		self.portconfig_dict = {}
		self.platform_specific_dict = {"x86_64-mlnx_msn2700-r0":self.msn2700_specific}
		self.default_lanes_per_port = []
		self.fpp = []
		self.fpp_split  =  {}
		self.num_of_fpp = 0
		self.num_of_lanes_dict = {"1" : 4, "2" : 2, "4" : 1}
		
		# Set up db connections
		###self.db = swsssdk.SonicV2Connector(host="127.0.0.1")
		###self.db.connect(self.db.CONFIG_DB)
		
		###self.configdb = swsssdk.ConfigDBConnector()
		###self.configdb.connect()

		###self.read_metadata()
		try:
			platform = subprocess.check_output("sonic-cfggen -H -v DEVICE_METADATA.localhost.platform",shell=True) #self.metadata['platform']
			self.platform = platform.rstrip()
		except KeyError:
			print ("Couldn't find platform info in CONFIG_DB DEVICE_METADATA", file=sys.stderr)
			exit()
		self.sku_name = None
		self.base_sku_name = None
		self.base_sku_dir = None
		self.base_file_path = None		
		self.new_sku_dir = None
		self.version_info = sonic_platform.get_sonic_version_info()
		self.build_version = format(self.version_info['build_version'])
		self.verbose = None

	def read_metadata(self):
		"""
		Redis database platform info
		"""
		try:
			self.metadata = self.db.get_all(self.db.CONFIG_DB, "DEVICE_METADATA|localhost" )
		except:
			print ("Error While trying to retrieve METADATA from CONFIG_DB", file=sys.stderr)
			exit()
			
	def sku_def_parser(self,sku_def) :
		try:
			f = open(str(sku_def),"r")
		except IOError:
			print ("Couldn't open file: " + str(sku_def), file=sys.stderr)
			exit()
		element = ET.parse(f)
		
		root = element.getroot()
		if (self.verbose):
			print ( "tag=%s, attrib=%s" % (root.tag, root.attrib))
		self.sku_name = root.attrib["HwSku"]
		self.new_sku_dir = DEFAULT_DEV_PATH+self.platform+"/"+self.sku_name+ '/'
		idx = 1
		for child in root:
			if child.tag == "Ethernet":
				for interface in child:
					for eth_iter in interface.iter():
						if eth_iter is not None:
							#self.portconfig_dict[eth_iter.get("Index")] = ["Ethernet"+eth_iter.get("Index"),[1,2,3,4], eth_iter.get("Speed"), eth_iter.get("InterfaceName"),  eth_iter.get("Index")]
							self.portconfig_dict[idx] = ["Ethernet"+eth_iter.get("Index"),[1,2,3,4], eth_iter.get("Speed"), eth_iter.get("InterfaceName"),  eth_iter.get("Index")]
							if (self.verbose):
								print ("sku_def_parser:portconfig_dict[",idx,"] -> ",self.portconfig_dict[idx])
							idx += 1

		f.close()

	def parse_deviceinfo(self,meta,hwsku):
		#port_speeds = {}
		idx = 1
		match = None
		for device_info in meta.findall(str(QName(minigraph_ns, "DeviceInfo"))):
			dev_sku = device_info.find(str(QName(minigraph_ns, "HwSku"))).text
			if dev_sku == hwsku :
				match = True
				interfaces = device_info.find(str(QName(minigraph_ns, "EthernetInterfaces"))).findall(str(QName(minigraph_ns1, "EthernetInterface")))
				for interface in interfaces:
					alias = interface.find(str(QName(minigraph_ns, "InterfaceName"))).text
					speed = interface.find(str(QName(minigraph_ns, "Speed"))).text
					index  = interface.find(str(QName(minigraph_ns, "Index"))).text
					port_name  = "Ethernet"+interface.find(str(QName(minigraph_ns, "PortName"))).text				
					#port_speeds[port_alias_map.get(alias, alias)] = speed
					self.portconfig_dict[idx] = [port_name,[1,2,3,4], speed, alias,  index]	
					if (self.verbose) :
						print ("parse_device_info(minigraph)--> ",self.portconfig_dict[idx])
					idx +=1
		if match is None :
			raise ValueError("Couldn't find a SKU ",hwsku, "in minigraph file")
			

	def minigraph_parser(self,minigraph_file) :
		root = ET.parse(minigraph_file).getroot()
		if (self.verbose):
			print ( "tag=%s, attrib=%s" % (root.tag, root.attrib))
		hwsku_qn = QName(minigraph_ns, "HwSku")
		for child in root:
			if (self.verbose) :
				print("TAG: ",child.tag, "TEXT: ",child.text)
			if child.tag == str(hwsku_qn):
				hwsku = child.text

		self.new_sku_dir = DEFAULT_DEV_PATH+self.platform+"/"+hwsku+ '/'
				
		for child in root:
			if child.tag == str(QName(minigraph_ns, "DeviceInfos")):
			#for device_info in meta.findall(str(QName(minigraph_ns, "DeviceInfo"))):
				self.parse_deviceinfo(child,hwsku)

		

		
	def split_analyze(self) :
		# Analyze the front panl ports split  based on the interfaces alias names
		# fpp_split is a hash with key=front panel port and values is a list of lists ([alias],[index])
		alias_index = PORTCONFIG_HEADER.index('alias')
		for idx,ifc in self.portconfig_dict.items():
			pattern = '^etp([0-9]{1,})([a-d]?)'
			m = re.match(pattern,str(ifc[alias_index]))
			if int(m.group(1)) not in self.fpp_split :
				self.fpp_split[int(m.group(1))] = [[ifc[alias_index]],[idx]] #1
			else:
				self.fpp_split[int(m.group(1))][0].append(str(ifc[alias_index])) #+= 1
				self.fpp_split[int(m.group(1))][1].append(idx)
			if (self.verbose) :
				print("split_analyze -> ",m.group(1), " : ", self.fpp_split[int(m.group(1))])
		self.num_of_fpp = len(self.fpp_split.keys())
		
	def get_default_lanes(self,sku_base) :
		self.base_sku_name = sku_base
		self.base_sku_dir = DEFAULT_DEV_PATH + self.platform + '/' + self.base_sku_name + '/'
		self.base_file_path = self.base_sku_dir + "port_config.ini"
		try:
			f = open(self.base_file_path,"r")
		except IOError:
			print ("Could not open file "+ self.base_file_path, file=sys.stderr)
			exit()
		line_header = f.next().split() # get the file header split into columns 
		if line_header[0] == "#" : del line_header[0] # if hashtag is in a different column, remove it to align column header and data
		alias_index = line_header.index('alias')
		lanes_index = line_header.index('lanes')
		pattern = '^etp([0-9]{1,})'
		for line in f:
			line_arr = line.split()
			m = re.match(pattern,line_arr[alias_index])
			self.default_lanes_per_port.insert(int(m.group(1))-1,line_arr[lanes_index])
			if (self.verbose) :
				print("get_default_lanes -> ",m.group(1), " : ", self.default_lanes_per_port[int(m.group(1))-1])
		f.close()
		
	def set_lanes(self) :
		#set lanes and index per interfaces based on split
		lanes_index = PORTCONFIG_HEADER.index('lanes')
		index_index = PORTCONFIG_HEADER.index('index')
		name_index = PORTCONFIG_HEADER.index('# name')
		
		for fp, values in self.fpp_split.items():
			splt_arr = sorted(values[0])
			idx_arr = sorted(values[1])

			splt = len(splt_arr)
			pattern = '(\d+),(\d+),(\d+),(\d+)'      #Currently the assumption is that the default(base) is 4 lanes

			m = re.match(pattern,self.default_lanes_per_port[fp-1])
			if (splt == 1) :
				self.portconfig_dict[idx_arr[0]][lanes_index] = m.group(1)+","+m.group(2)+","+m.group(3)+","+m.group(4) 
				self.portconfig_dict[idx_arr[0]][index_index] = str(fp)
				self.portconfig_dict[idx_arr[0]][name_index] = "Ethernet"+str((fp-1)*4)
				if (self.verbose) :
					print ("set_lanes -> FP: ",fp, "Split: ",splt)
					print ("PortConfig_dict ",idx_arr[0],":", self.portconfig_dict[idx_arr[0]])
			elif (splt == 2) :
				self.portconfig_dict[idx_arr[0]][lanes_index] = m.group(1)+","+m.group(2) 
				self.portconfig_dict[idx_arr[1]][lanes_index] = m.group(3)+","+m.group(4)
				self.portconfig_dict[idx_arr[0]][index_index] = str(fp) 
				self.portconfig_dict[idx_arr[1]][index_index] = str(fp)
				self.portconfig_dict[idx_arr[0]][name_index] = "Ethernet"+str((fp-1)*4) 
				self.portconfig_dict[idx_arr[1]][name_index] = "Ethernet"+str((fp-1)*4+2)
				if (self.verbose) :
					print ("set_lanes -> FP: ",fp, "Split: ",splt)
					print ("PortConfig_dict ",idx_arr[0],":", self.portconfig_dict[idx_arr[0]])
					print ("PortConfig_dict ",idx_arr[1],":", self.portconfig_dict[idx_arr[1]])
			elif (splt == 4) :
				self.portconfig_dict[idx_arr[0]][lanes_index] = m.group(1) 
				self.portconfig_dict[idx_arr[1]][lanes_index] = m.group(2) 
				self.portconfig_dict[idx_arr[2]][lanes_index] = m.group(3) 
				self.portconfig_dict[idx_arr[3]][lanes_index] = m.group(4)
				self.portconfig_dict[idx_arr[0]][index_index] = str(fp) 
				self.portconfig_dict[idx_arr[1]][index_index] = str(fp) 
				self.portconfig_dict[idx_arr[2]][index_index] = str(fp) 
				self.portconfig_dict[idx_arr[3]][index_index] = str(fp)
				self.portconfig_dict[idx_arr[0]][name_index] = "Ethernet"+str((fp-1)*4) 
				self.portconfig_dict[idx_arr[1]][name_index] = "Ethernet"+str((fp-1)*4+1) 
				self.portconfig_dict[idx_arr[2]][name_index] = "Ethernet"+str((fp-1)*4+2) 
				self.portconfig_dict[idx_arr[3]][name_index] = "Ethernet"+str((fp-1)*4+3)
				if (self.verbose) :
					print ("set_lanes -> FP: ",fp, "Split: ",splt)
					print ("PortConfig_dict ",idx_arr[0],":", self.portconfig_dict[idx_arr[0]])
					print ("PortConfig_dict ",idx_arr[1],":", self.portconfig_dict[idx_arr[1]])
					print ("PortConfig_dict ",idx_arr[2],":", self.portconfig_dict[idx_arr[2]])
					print ("PortConfig_dict ",idx_arr[3],":", self.portconfig_dict[idx_arr[3]])
		self.platform_specific()	
	
	

		
	def create_port_config(self) :
		#create a port_config.ini file based on the sku definition 
		if not os.path.exists(self.new_sku_dir):
			print("Error - path:", self.new_sku_dir, " doesn't exist",file=sys.stderr)
			exit()
			
		try:
			f = open(self.new_sku_dir+"port_config.ini","w+")
		except IOError:
			print ("Could not open file "+ self.new_sku_dir+"port_config.ini", file=sys.stderr)
			exit()
		header = PORTCONFIG_HEADER # ["name", "lanes", "alias", "index"]
		port_config = []
		for line in self.portconfig_dict.values():
			port_config.append(line)
		 
		port_config.sort(key=lambda x: (int(re.search(('\d+'),x[0]).group(0)))) # sort the list with interface name
		f.write(tabulate(port_config, header,tablefmt="plain"))
		f.close()
	
	def print_port_config(self) :
		#print a port_config.ini file based on the sku definition 
		
		header = PORTCONFIG_HEADER # ["name", "lanes", "alias", "index"]
		port_config = []
		for line in self.portconfig_dict.values():
			port_config.append(line)
		 
		port_config.sort(key=lambda x: (int(re.search(('\d+'),x[0]).group(0)))) # sort the list with interface name
		print(tabulate(port_config, header,tablefmt="plain"))
		
		
	def create_sku_dir(self) :
		# create a new SKU directory based on the base SKU
		if (os.path.exists(self.new_sku_dir)):
			print ("SKU directory: "+self.new_sku_dir+ " already exists\n Please use -r flag to remove the SKU dir first", file=sys.stderr)
			exit()
		try:
			shutil.copytree(self.base_sku_dir, self.new_sku_dir)
		except OSError as e:
			print (e.message, file=sys.stderr)
	
	def remove_sku_dir(self) :
		# remove SKU directory 
		if (self.base_sku_dir == self.new_sku_dir) :
			print ("Removing the base SKU" + self.new_sku_dir + " is not allowed", file=sys.stderr)
			exit()
		try:
			if not os.path.exists(self.new_sku_dir):
				print ("Trying to remove a SKU "+ self.new_sku_dir + " that doesn't exists, Ignoring -r command")
			while True:
				answer = raw_input("You are about to permanently delete the SKU "+ self.new_sku_dir+" !! \nDo you want to continue (Yes/No)?") 
				if (answer == "Yes" or answer == "No"):
					break
				else:
					print("Valid answers are Yes or No")
			if (answer == "Yes") :
				shutil.rmtree(self.new_sku_dir)
				print ("SKU directory: "+ self.new_sku_dir + " was removed")
			else :
				print ("SKU directory: "+ self.new_sku_dir + " was NOT removed")
		except OSError as e:
			print(e.message, file=sys.stderr) 
					
	def platform_specific(self) :
		func = self.platform_specific_dict.get(self.platform, lambda: "nothing")
		return func()
		
		
	def msn2700_specific(self) :
		for fp, values in self.fpp_split.items():
			splt_arr = sorted(values[0])
			idx_arr = sorted(values[1])
			splt = len(splt_arr)
			fp=fp
			try :
				if ((fp%2) == 1 and splt == 4) :
					next_fp = fp+1
					if (next_fp not in self.fpp_split) :
						continue
					next_fp_idx_arr = sorted(self.fpp_split[next_fp][1])
					for i in next_fp_idx_arr :
						if (self.verbose) :
							print ("msn2700_specific -> Removing ", self.portconfig_dict[i])
						self.portconfig_dict.pop(i)
					print ("MSN2700 - Front panel port ",next_fp, " should be removed due to port ",fp,"Split by 4")
					raise  ValueError()
					#continue
				elif ((fp%2) == 0 and splt == 4) :
					#for idx in idx_arr :
					#	self.portconfig_dict.pop(idx,None )
					print ("MSN2700 -  even front panel ports (",fp,") are not allowed to split by 4")
					raise  ValueError()
			except ValueError:
				print ("Error - Illegal split by 4 ", file=sys.stderr)
				exit()

		
	
	def l2_mode(self,l2_sku) :
		if not os.path.exists(DEFAULT_DEV_PATH+self.platform+"/"+l2_sku):
			print ("Error - path:", l2_sku, " doesn't exist", file=sys.stderr)
			exit()
		print( "Starting L2 mode configuration based on "+l2_sku+" SKU")	
		cfg_db_str = "\n{\n\t\"DEVICE_METADATA\": {\n\t\t\"localhost\": {\n\t\t\t\"hostname\": \"sonic\"\n\t\t}\n\t}\n}\n"

		subprocess.call("cat <<EOF | sudo config reload /dev/stdin -y" + cfg_db_str, shell=True)
		subprocess.call("sudo sonic-cfggen -H --write-to-db ", shell=True)
		subprocess.call("sonic-cfggen -t /usr/local/lib/python2.7/dist-packages/usr/share/sonic/templates/l2switch.j2 -p -k" + l2_sku + " | sudo config load /dev/stdin -y", shell=True ) 
		subprocess.call("sudo config save -y ", shell=True)
		subprocess.call("sudo systemctl restart swss ", shell=True)

		print( "Finished L2 mode configuration based on "+l2_sku+" SKU")
		
def main():
	parser = argparse.ArgumentParser(description='Create a new SKU',
									version='1.0.0',
									formatter_class=argparse.RawTextHelpFormatter)
	group = parser.add_mutually_exclusive_group()
	group.add_argument('-f', '--file', action='store', help='SKU definition from xml file. -f OR -m must be provided when creating a new SKU', default=None)
	group.add_argument('-m', '--minigraph_file', action='store', help='SKU definition from minigraph file. -f OR -m must be provided when creating a new SKU', default=None)
	parser.add_argument('-b', '--base', action='store', help='SKU base definition  ', default=None)
	parser.add_argument('-r', '--remove', action='store_true', help='Remove SKU folder')
	parser.add_argument('-c', '--cmd', action='store', choices=['new_sku_only', 'l2_mode_only', 'new_sku_l2'], help='Choose action to preform (Generate a new SKU, Configure L2 mode, Both', default="new_sku_only")
	parser.add_argument('-s', '--sku', action='store', help='SKU name to be used when creating a new SKU or for  L2 configuration mode', default=None)
	parser.add_argument('-p', '--print', action='store_true', help='Print port_config.ini without creating a new SKU', default=False)
	parser.add_argument('-vv', '--verbose', action='store_true', help='Verbose output', default=False)
	args = parser.parse_args()
	l2_mode = False
	sku_mode = False
	sku_name = None
	base = None
	try:
		sku = SkuCreate()
		sku.verbose = args.verbose
		if args.cmd == "l2_mode_only":
			l2_mode = True
			sku_mode = False
		elif args.cmd == "new_sku_l2":
			l2_mode = True
			sku_mode = True
		else :
			l2_mode = False
			sku_mode = True
			
		if args.base:
			base = args.base
		else :
			f=open(DEFAULT_DEV_PATH + sku.platform + '/' + "default_sku","r")
			base=f.read().split()[0]
			
		if args.file:
			sku.sku_def_parser(args.file)
		elif args.minigraph_file:
			sku.minigraph_parser(args.minigraph_file)
		elif sku_mode:
			print ("SKU definition file was not provided (-f OR -m flags) while trying to create a new SKU.\n Only l2_mode_only command can omit the definition file", file=sys.stderr)
			exit() 
		if sku_mode :
			if args.remove:
				sku.remove_sku_dir()
				return
			sku.get_default_lanes(base)
			sku.split_analyze()
			sku.set_lanes()
			if args.print:
				sku.print_port_config()
			else:
				sku.create_sku_dir()
				sku.create_port_config()
				print ("Created a new sku (Location: " + sku.new_sku_dir+")")
			
		if l2_mode : ##If No SKU name provided by -s then if -file exists, use the sku from the file otherwise use base 
			if args.sku is None :
				if args.file is None :
					if args.base is None :
						print ("Error in configuring L2 Mode: Must provide a SKU Name . Use: -sku <SKU_NAME>, -b <SKU_NAME> or -f <SKU DEF File>\n", file=sys.stderr)
						exit()
					else :
						sku_name = args.base
				else :
					sku_name = sku.sku_name 
			else: 
				sku_name = args.sku
			sku.l2_mode(sku_name)
		
	except Exception :
		traceback.print_exc(file=sys.stderr)
		sys.exit(1)

if __name__ == "__main__":
    main()
