import select
import socket
import sys
import queue

#create our Broker TCP socket
broker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
broker.setblocking(0)   #Set Blocking to false

#Bind socket to port
broker.bind(("192.168.1.40", 80))
print ("Bind Successful")

broker.listen(5) # listening for a connections

#select takes 3 lists as params: input, output, Those that may have errors (a combo of the previous)

inputs = [broker]   #expect to get requests from the broker           //would also accept input data from sensors here, will check video and audio
outputs = []        #Devices to forward requests to

#create message queue
message_queues = {} 


#main will loop forever and let select handle data

while inputs:     #remember broker is an input as it listens for data hence if its on will loop
    print("Entered main loop")

    readable, writable, exceptional = select.select(inputs, outputs, inputs)        #will play around with the last param depending on error activity from use

    #readable is a list of sockets which have incoming data available and ready to read from
    #writable a list of sockets ready to be written too
    #exceptional is a list of sockets in which an error occured


    #Handling reading in data first
    for connection in readable:
        
        #handle if its a message to the broker i.e. a new connection
        if connection is broker:
            
            client, client_address = connection.accept()        #accept connection  
            client.setblocking(0)                           #set blocking false
            inputs.append(connection)
           
            message_queues[connection] = queue.Queue() #research this step more looks like we will recieve all messages at a later stage

        #devices with which communication has already been establish i.e. where we will read in the requests and the sensor data
        else:
            data = connection.recv(1024)      #recieve 1024 bytes of data, obviously we can change this to our needs

            #so this my propsed way of handling string input i.e. non audio and video

            #assuming we use underscores an input format of  x_y_z_data 
            #data is the data transmitted, i.e. a message "on"
            #x is a 0 or 1, 1, means a device that has previously connected i.e. should the Pi store the IP , will be handled on device side
            #z is a 0 or 1, 1, means new request, i.e. from the app (database), 0 would indicate sensor or any data we are recieving directly from a device
            #y is device name with a set character limit

            #so this x_y_z is what i mean by encodeing and then what is below is essentially decoding


            if data:
                commands = data.decode().split("_")  #So to avoid confusion note this decode() is the tcp vibes it will return x_y_z_data
                #Index 0 = x
                #Index 1 = y
                #Index 2 = Device Name
                #index 3 = data

                if commands[0] == 0:
                    
                    #Pi needs to store IP data and link to device name i.e. commands[2] in a dictionary that is stored on the Pi
                    #create message to send later in the outputs section
                    message = "Recieved"
                    message_queues[connection].put(message)

                    #add device to outputs
                    if connection not in outputs:
                        outputs.append(connection)



                if commands[1] == 0:
                    
                    #Handle Sensors
                    #create message to send
                    message = "Recieved"
                    message_queues[connection].put(message)

                

                else: 
                    
                    #Handle Requests
                    #create message to send
                    message = "Recieved"
                    message_queues[connection].put(message)

            else:   
                
                #a socket which is readable which has not sent more data is handled here, should connection close?
                if connection in outputs:
                    outputs.remove(connection)
                    connection.close()
                    del message_queues[connection]

        
    for connection in writable:
        try:
            message = message_queues[connection].get_nowait()   #get the message from the queue which is set in the read phase

        except queue.Empty():
            #nothing to write to devices
            pass
        
        else:
            connection.send(message)    #send message to device


    for connection in exceptional:
        pass
        #deal with errors once we learn how 
        #for now we should probs just close the socket to avoid more complications on errors
        connection.close()
