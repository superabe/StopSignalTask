import socketserver
import threading
import cv2
import imutils
import pickle
import struct
import time

class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def __init__(self, request, client_address, server, C_TYPE_FORMAT = 'I'):
        self.myCamera = cv2.VideoCapture(0)
        self.C_TYPE_FORMAT = C_TYPE_FORMAT
        print('Connection Established')
        self.start_time = 0
        self.current_time = 0
        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)

    def captureVideo(self, trialNum = 0, current_time = 0):
        # read frame from the camera
        if(self.myCamera.isOpened()):
            ret, frame = self.myCamera.read()

            # resize the frame to 480 width while keeping the ratio
            frame = imutils.resize(frame, width=480)
            # print trial number on the screen
            cv2.putText(frame, 'Trial Finished: '+str(trialNum), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA )
            # transform seconds to minutes and print it on the screen
            current_time = current_time // 60
            cv2.putText(frame, 'Time Elapsed: '+str(current_time)+' min', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA )
            # image compression
            r, frame = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 30])
            return((r, frame))

    def captureTrialNum(self):
        pass

    def pack_data(self, data):
        # pickle data
        pickled_data = pickle.dumps(data)

        # add the length of the frame at the beginning
        data_to_send = struct.pack(self.C_TYPE_FORMAT, \
                                   len(pickled_data)) \
                                   +pickled_data
        return(data_to_send)

    def handle(self):
        # request handler
        while True:
            # get the data to send
            trialNum = self.server.getTrialNum()
            timeElapsed = self.server.getTimeSinceStart()
            r, frame = self.captureVideo(trialNum, timeElapsed)
            data_to_send = self.pack_data(frame) + self.pack_data(trialNum)
            self.request.sendall(data_to_send)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass
