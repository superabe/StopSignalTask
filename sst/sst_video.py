import socket
import sys
import time
import cv2
import pickle
import struct

def displayVideo(HOST='localhost', PORT=9999, C_TYPE_FORMAT = 'I'):
    # Create a socket (SOCK_STREAM means a TCP socket)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Connect to server and send data
        sock.connect((HOST, PORT))
        # Initialized an empty byte
        data = b''
        # Get the size of header information
        header_info_size = struct.calcsize(C_TYPE_FORMAT)
        counter = 0
        try:
            while True:
                # get header info first
                while len(data) < header_info_size:
                    data += sock.recv(512)
                header_info = data[:header_info_size]
                # unpack the header_info and get the size of the frame
                header_info = struct.unpack(C_TYPE_FORMAT, header_info)
                data_size = header_info[0]

                # get the rest data until the length of the data is reached
                while len(data) < header_info_size + data_size :
                    data += sock.recv(512)
                pickled_frame = data[header_info_size:(header_info_size+ \
                                                       data_size)]
                frame = pickle.loads(pickled_frame)
                if type(frame) != int:
                    frame = cv2.imdecode(frame, 1)
                    cv2.imshow('frame',frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                data = data[(header_info_size+data_size):]

        except KeyboardInterrupt:
            pass
