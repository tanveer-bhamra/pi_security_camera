import cv2
import time
import datetime
import smtplib  # for sending emails
import ssl
import copy
import email
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import glob
import shutil
import multiprocessing as mp



def security_cam():
    """security camera using face and body motion detection to 
       trigger recording and write it to a mp4 file once finished
    """
    cap = cv2.VideoCapture(0)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    body_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_fullbody.xml")

    detection = False
    detection_stopped_time = None
    timer_started = False
    SECONDS_TO_RECORD_AFTER_DETECTION = 5

    frame_size = (int(cap.get(3)), int(cap.get(4)))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    while True:
        _, frame = cap.read()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        bodies = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) + len(bodies) > 0:
            if detection:
                timer_started = False
            else:
                detection = True
                current_time = datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
                out = cv2.VideoWriter(
                    f"{current_time}.mp4", fourcc, 20, frame_size)
                print("Started Recording!")
        elif detection:
            if timer_started:
                if time.time() - detection_stopped_time >= SECONDS_TO_RECORD_AFTER_DETECTION:
                    detection = False
                    timer_started = False
                    out.release()
                    print('Stop Recording!')
            else:
                timer_started = True
                detection_stopped_time = time.time()

        if detection:
            out.write(frame)

        # for (x, y, width, height) in faces:
        #    cv2.rectangle(frame, (x, y), (x + width, y + height), (255, 0, 0), 3)

        cv2.imshow("Camera", frame)

        if cv2.waitKey(1) == ord('q'):
            break

    out.release()
    cap.release()
    cv2.destroyAllWindows()

def email_notifier():
    """to send email notification with video attachment when motion 
       detection has been activated"""
    
    sending = True  # boolean to enable checks fo new videos and sends email on periodic basis
    password = "Scotland145!" #input("Type password: ")
    while sending == True:
        port = 465  # for SSL
        smtp_server = "smtp.gmail.com"
        sender_email = "tan.singh.pi@gmail.com"
        reciever_email = copy.copy(sender_email)
        
        # create a message object
        message = MIMEMultipart()

        # add parameters for message
        subject = "Security camera video notification!!!"
        body = "Your Pi security camera has detected and recorded motion -  please see the attached video" # message sent in email

        message["To"] = reciever_email
        message["From"] = sender_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

    
        # create a list of video files to be sent
        video_file_paths = "/Users/tanny/OneDrive/Documents/projects/Tutorials/opencv/*.mp4"
        video_files = glob.glob(video_file_paths)  # creates a list of video file paths
        sent_videos_path = "/Users/tanny/OneDrive/Documents/projects/Tutorials/opencv/sent_videos"  # move sent video files into new directory

        # lOGIC - send email notification if a video has been recorded, else print message
        if len(video_files) > 0: 
            video_file = video_files[0]

            attachment = open(video_file, "rb")
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            attachment.close()

            # Encode file in ASCII characters to send by email
            encoders.encode_base64(part)

            # Add header as key/value pair to attachment part
            part.add_header(
                "Content-Disposition",
                f"attachment; filename  = {video_file}",
            )

            # Add attachment to message and convert message to string
            message.attach(part)
            text = message.as_string()

            context = ssl.create_default_context() # makes sure everything is legit and ensures secure communication by encryption

            # sets up secure (encrypted) connection session
            with smtplib.SMTP_SSL(host=smtp_server, port=port, context=context) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, reciever_email, text)
                server.quit()

            # Move the sent file into the sent_videos directory  
            shutil.move(video_file, sent_videos_path)

        else:
            print("The security camera has not detected any motion and no videos have been recorded")
        
          # clears list of filepaths so it can be repopulated in next itteration
        time.sleep(60)

p1 = mp.Process(target = security_cam)
p2 = mp.Process(target=email_notifier)

# start processes
if __name__ == "__main__":
    p1.start()
    p2.start()
