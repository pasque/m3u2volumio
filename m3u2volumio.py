#!/usr/bin/python3


### User Environmental Settings ~~~~~~~~~~

vmusic_path='mnt/NAS/MusicShare/'	# Path of the music files as seen from the Volumio server including the Alias (must be same for all Volumio systems and no leading /)
lmusic_path='D:\Music\iTunes\iTunes Media\Music\\'	# Path of the music files as seen from the local system here it is a Windows system so we also have to replace \ with / later
vservers='garage' # List of Volumio servers [IP of Server Name] to upload the playlist separated by commas
vuser='volumio' # Volumio username for SSH login (assumes that ssh authorized key is configured on Volumio system (reference https://www.raspberrypi.org/documentation/remote-access/ssh/passwordless.md)
vpl_www_file='my-web-radio' # File name of the web radio favourite list; options 'my-web-radio' (My Web Radios) or 'radio-favourites' (Favorite Radios)

verbose=1 # level of messages shown in stdout: 0 [disalbed], 1 [warn/error], 2 [info], 3 [debug]

## Edit should not be required below this line

### Declarations ~~~~~~~~~~
vpl_music_path='/data/playlist/' # Path of the music playlist files for the Volumio server (must be same for all Volumio systems)
vpl_www_path='/data/favourites/' # Path of the web radio playlist files for the Volumio server (must be same for all Volumio systems)


### Dependencies ~~~~~~~~~~

import sys, os
from collections import OrderedDict
import paramiko

### Verison information ~~~~~~~~~~

version = 0.3
changelog = {}
changelog[0.1] = "First Release"
changelog[0.2] = "Added handling for non-ascii characters and changelog"
changelog[0.3] = "Added stdout messaging control\n\t Added feature to upload the playlist to Volumio server(s) via SSH\n\t Added function to replace local path with Volumio path\n\t Fixed Web Radio Favourites format\n\t Supports UTF-8 encoded file names"
changelog[0.4] = "Added replace for changing \ to / given difference between Windows naming and NAS naming and made permanent change in artist - title naming for itunes playlists"


### Defined Functions ~~~~~~~~~~

## Function to put Playlist on Volumio via SSH
def put_file_ssh(machinename, username, dirname, filename, data):
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(machinename, username=username)
	sftp = ssh.open_sftp()
	try:
		sftp.mkdir(dirname)
	except IOError:
		pass
	f = sftp.open(dirname + '/' + filename, 'w')
	f.write(data)
	f.close()
	ssh.close()
	
## Fucntion to check for extended or simple format
def check_m3u(data):
	''.join(data)
	if data[0] == '#EXTM3U':
		if not (len(data) % 2) == 1:
			raise RuntimeError('Even number of entries! Forgotten declaration or uri?')
		return 'extended'
	else:
		return 'simple'

## Function to process extended playlist with EXT tags
def gen_extended(data):
	data = data[1:]
	parsed_m3u  = OrderedDict()
	trigger_www = {}

	for n in range(int(len(data)/2)):
		title = data[2*n].split(',')[1]
		uri = data[2*n+1]
		parsed_m3u[title] = uri

		if 'http://' in uri or 'https://' in uri:
			trigger_www[title] = 1
		else:
			trigger_www[title] = 0

	return parsed_m3u, trigger_www

## Process for simple m3u playlist, without EXT tags
def gen_simple(data):
	parsed_m3u  = OrderedDict()
	trigger_www = {}

	for l in data:
		title = l.split('/')[-1]
		uri = l
		parsed_m3u[title] = uri
		if 'http://' in uri or 'https://' in uri:
			trigger_www[title] = 1
		else:
			trigger_www[title] = 0

	return parsed_m3u, trigger_www

if __name__ == "__main__":

## Argument parser ~~~~
	if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
		print('Usage:')
		print('\t{} <filename.m3u>'.format(sys.argv[0]))
		print('\t-c, --changelog')
		print('\t-h, --help')
		print('\t-v, --version')
		print('Edit user environmental variables in {} before running.'.format(sys.argv[0]))
		sys.exit(0)
    
	if len(sys.argv) > 1 and sys.argv[1] in ['-v', '--version']:
		print("Version {}".format(version))
		sys.exit(0)
    
	elif len(sys.argv) > 1 and sys.argv[1] in ['-c', '--changelog']:
		for key in changelog:
			print(key,"\t",changelog[key])
		sys.exit(0)

	if not len(sys.argv) == 2:
		raise ValueError('Wrong number of arguments!\nUsage: {} <filename.m3u>'.format(sys.argv[0]))

	elif not os.path.isfile(sys.argv[1]):
		raise ValueError('File {} not found!'.format(sys.argv[1]))
    
	elif not sys.argv[1].endswith('.m3u'):
		raise ValueError('Not a .m3u file!')

## Convert m3u entries to Voluimo format ~~~~
	with open(sys.argv[1], 'r') as f:
		data = f.readlines()

	data = [l.strip() for l in data]    
	data = list(filter(None, data))

	m3u_type = check_m3u(data)

	if m3u_type == 'extended':
		data, trigger_www = gen_extended(data)
	elif m3u_type == 'simple':
		data, trigger_www = gen_simple(data)

	output = []

	for key in data:
		if trigger_www[key]:
			output.append('{' + '"service":"webradio","name":"' + key + '","name":"' + key + '","uri":"' + data[key] + '"}')

		else:
			if '-' in key and key.count('-') == 1:
				artist = key.split('-')[1].strip()
				title = key.split('-')[0].strip()

				# Removing file extension from Artist - Title string
				title_temp = '.'.join(title.split('.')[:-1])
				if not title_temp == '':
					title = title_temp
                
				# Changing the local path to the volumio path
				uri = data[key].replace(lmusic_path, vmusic_path, 1).replace('\\', '/')
				output.append('{' + '"service":"mpd","title":"' + title + '","artist":"' + artist + '","uri":"' + uri + '"}')

			else:
				# Assuming file extension: Removing it
				title_temp = '.'.join(key.split('.')[:-1])
				if not title_temp == '':
					title = title_temp

				# Changing the local path to the volumio path
				uri = data[key].replace(lmusic_path, vmusic_path, 1).replace('\\', '/')
				output.append('{' + '"service":"mpd","title":"' + title + '","uri":"' + uri + '"}')
			
## Uploading Volumio formatted playlist to Volumio server(s) ~~~~
	if verbose >= 3:	print('Debug: Volumio formatted playlist:\n[' + ',\n'.join(output) + ']')
	data = ('[' + ',\n'.join(output) + ']\n') #.encode('ascii')
	if 'http' in data:
		vpl_path = vpl_www_path	# Setting path to favourites for www playlists
		vpl_name = vpl_www_file 
	else:
		vpl_path = vpl_music_path	# Setting path to playlist for all other
		vpl_name_tmp = (os.path.basename(sys.argv[1]))		# Extract Volumio Playlist name from m3u playlist file
		vpl_name = vpl_name_tmp.rsplit('.',1)	# Removing extension
		vpl_name = vpl_name[0]

	data = data.encode('utf-8')

	# Upload to each Volumio server
	vsvr = vservers.split(',')
	for s in range(len(vsvr)):
		svr = vsvr[s].strip()
		if verbose >= 3:	print('Debug: Uploading playlist "' + vpl_name + '" to Volumio server ' + svr + vpl_path + ' via SSH')
		try:
			put_file_ssh(svr, vuser, vpl_path, vpl_name , data) # existing files will be clobbered
			if verbose >= 2:	print('Info: Playlist "' + vpl_name + '" has been uploaded to Volumio server ' + svr + vpl_path + vpl_name + ' via SSH')
		except:
			if verbose >= 1:	print('\nError: Cannot connect to "' + svr + '" check user-env settings and network connectivity!\n')
			
