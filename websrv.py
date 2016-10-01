import socket
import errno
import os
import signal

# Networking variables
SERVER_ADDRESS = (HOST, PORT) = '', 8888
REQUEST_QUEUE_SIZE = 5

# Configuration variables
rootdir = "/srv/http"
homepagepath = "/index.html"
pagenotfoundpath = rootdir + "/notfound.html"

# Return the response based on the request
def handlerequest(request):
	print("\n-----------------------\n## New Request ##")
	print(request)
	print("\n## Loading Response ##")
	http_response = b"""\
HTTP/1.1 200 OK

""" + getfiledata(request)
	return http_response


# Process to remove zombie children
def grim_reaper(signum, frame):
	while True:
		try:
			pid, status = os.waitpid(
				-1,          # Wait for any child process
				os.WNOHANG  # Do not block and return EWOULDBLOCK error
			)
		except OSError:
			return

		if pid == 0:  # no more zombies
			return


# Read the file requested
def getfiledata(request):
	# Get the path of the requested file relative to the root dir
	relativepath = str(request).split(' ')[1]
	if relativepath == "/":
		relativepath = homepagepath
	
	# Read the requested file
	fullpath = rootdir + relativepath
	if os.path.isfile(fullpath): # If the file exists
		print("Loading file " + fullpath + "\n-----------------------")
		f = open(fullpath, 'rb')
		data = f.read()
		f.close()
	else:
		print("Requested file not found\n-----------------------")
		f = open(pagenotfoundpath, 'rb')
		data = f.read()
		f.close()
	return data


# Main server code
def serve():
	# Create listener socket
	listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	listen_socket.bind(SERVER_ADDRESS)
	listen_socket.listen(REQUEST_QUEUE_SIZE)
	print('Serving HTTP on port {port} ...'.format(port=PORT))
	
	# Bind SIGCHILD signal to grim_reaper function to remove completed child servers
	signal.signal(signal.SIGCHLD, grim_reaper)
	
	# Main listening loop
	while True:
		# Accept next connection
		try:
			client_connection, client_address = listen_socket.accept()
		except IOError as e:
			code, msg = e.args
			# restart 'accept' if it was interrupted
			if code == errno.EINTR:
				continue
			else:
				raise
		
		# Put the connection in a new child process
		pid = os.fork()
		
		if pid == 0:  # Code if process is a new child slave
			listen_socket.close()  # Close child copy of socket listener
			request = client_connection.recv(1024) # Recieve the clients request
			response = handlerequest(request) # Handle the request of the client
			client_connection.sendall(response) # Send the response the client
			client_connection.close() # Close the connection to the client
			os._exit(0) # Exit the child process
		else:  # Code if process is the parent
			client_connection.close()  # Close the connection and wait for the next
		
		
if __name__ == '__main__':
	serve()
