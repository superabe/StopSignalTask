import socketserver
import threading
import cv2
import imutils
import pickle
import struct

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
        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)

    def captureVideo(self, trialNum = 0):
        # read frame from the camera
        if(self.myCamera.isOpened()):
            ret, frame = self.myCamera.read()

            # resize the frame to 480 width while keeping the ratio
            frame = imutils.resize(frame, width=480)
            cv2.putText(frame, 'Trial: '+str(trialNum), (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA )
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
        #counter = 0
        while True:
            # get the data to send
            #counter += 1
            trialNum = self.server.getTrialNum()
            r, frame = self.captureVideo(trialNum)
            data_to_send = self.pack_data(frame)
            #if counter/100>1:
            #    counter = 0
            #    trialNum = self.server.getTrialNum()
            #    data_to_send += self.pack_data(trialNum)
            self.request.sendall(data_to_send)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass
