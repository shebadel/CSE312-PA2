import os
import socketserver
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://mongo:27017/")
db = client["comment_db"]
comments_collection = db["comments"]

def get_content_length(file_path):
        file_size = os.path.getsize(file_path)
        return str(file_size).encode('utf-8')

def escape_html(text):
    #Escapes the HTML special characters in the given text
    html_escape_table = {
        "&": "u;",
        '"': "lost;",
        "'": "get;",
        ">": "outta;",
        "<": "here;",
        "/": "chump;",
    }
    return "".join(html_escape_table.get(c, c) for c in text)


image_counter = 0


class MyTCPHandler(socketserver.BaseRequestHandler):
    socketserver.TCPServer.allow_reuse_address = True

    def parse_request(self, request_str):
        headers = {}
        request_lines = request_str.split("\r\n")
        if len(request_lines) > 0:
            first_line = request_lines[0].split(" ")
            if len(first_line) == 3 and first_line[0] == "GET":
                headers["request_method"] = first_line[0]
                headers["path"] = first_line[1]
                headers["protocol"] = first_line[2]
                
                for line in request_lines[1:]:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        headers[key.strip()] = value.strip()

            if first_line[0] == "POST":
                headers["request_method"] = first_line[0]
                headers["path"] = first_line[1]
                content_length = headers.get("Content-Length")
                if content_length:
                    body = request_str.split("\r\n\r\n")[1]
                    if len(body) == int(content_length):
                        headers["body"] = body
                        content_type_header = headers.get("Content-Type")
                        if content_type_header:
                            content_type, *params_str = content_type_header.split(";")
                            headers["Content-Type"] = content_type
                            for param_str in params_str:
                                param_parts = param_str.strip().split("=")
                                if len(param_parts) == 2 and param_parts[0] == "boundary":
                                    headers["boundary"] = param_parts[1].strip().strip('"')

        return headers

    def handle(self):
        global image_counter
        global com_and_pic
        global image_filename
        global comment_str
        #self.data = self.request.recv(2048).strip() #returns 2048 bytes of data
        #print(self.data)

        received_data = self.request.recv(2048)
        print(received_data)

        request_str = received_data.decode("utf-8")
        headers = self.parse_request(request_str)
        request_method = headers.get("request_method")
        path = headers.get("path")

        if request_method == "GET" and path == "/hello":
            self.request.send('HTTP/1.1 200 OK\r\nContent-Length: 11\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nHello World'.encode())
        elif request_method == "GET" and path == "/hi":
            self.request.send('HTTP/1.1 301 Moved Permanently\nLocation: /hello\r\nContent-Length: 0\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nHello World'.encode())
        elif request_method == "GET" and path == "/":
            # Get the comments from the database
            comments = []
            images = []
            for comment in comments_collection.find():
                if comment["type"] == "comment":
                    comments.append(comment["comment_str"])
                elif comment["type"] == "file":
                    images.append(comment["image_filename"])

            file_path = os.path.join(os.getcwd(), "index.html")
            with open(file_path, "rb") as f:
                html = f.read()

                # Insert the comments into the HTML template
                comments_html = ""
                for comment in comments:
                    comments_html += f'<p class="comment">{comment}</p>'

                html.replace(b"<!-- COMMENTS -->", comments_html.encode())


                images_html = ""
                for image in images:
                        images_html += f'<img src="{image}" alt="uploaded image"/>'

                html.replace(b"<!-- IMAGES -->", images_html.encode())

                # Send the HTML template as the HTTP response
                content_length = get_content_length(file_path)
                response = f"HTTP/1.1 200 OK\r\nContent-Length: {content_length}\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"
                self.request.sendall(response.encode() + html)
        
        elif request_method == "GET" and path == "/functions.js":
            file_path = os.path.join(os.getcwd(), "functions.js")
            content_length = get_content_length(file_path)
            response = f"HTTP/1.1 200 OK\r\nContent-Length: {content_length}\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/javascript; charset=utf-8\r\n\r\n"
            with open(file_path, "rb") as f:
                content = f.read()
                self.request.sendall(response.encode() + content)
        elif request_method == "GET" and path == "/style.css":
            file_path = os.path.join(os.getcwd(), "style.css")
            content_length = get_content_length(file_path)
            response = f"HTTP/1.1 200 OK\r\nContent-Length: {content_length}\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/css; charset=utf-8\r\n\r\n"
            with open(file_path, "rb") as f:
                content = f.read()
                self.request.sendall(response.encode() + content)
        elif request_method == "GET" and path.startswith("/image/"):
            file_name = path.split("/")[-1]
            file_path = os.path.join(os.getcwd(), "image", file_name)
            content_length = get_content_length(file_path)
            response = f"HTTP/1.1 200 OK\r\nContent-Length: {content_length}\r\nX-Content-Type-Options: nosniff\r\nContent-Type: image/jpg\r\n\r\n"
            with open(file_path, "rb") as f:
                content = f.read()
                self.request.sendall(response.encode() + content)

        elif request_method == "POST" and path == "/image-upload":

            # declare buffer
            # then parse through the headers as utf -8 get content length
            # split at '\r\n\r\n' to seperate the headers from the body
            # add body as bytes to buffer
            # buffer will hold everything after the headers, entire body

            # while the length of the buffer is less than the content length
            # constantly calling recieved data, adding byte by byte to buffer
            # then take length of buffer and check the condition
            # else outside of while loop, finding the difference between the current length of the buffer and content legnth, to tell how much is remaining outside of request, then request from recieved data and add that to the buffer

            buffer = b""
            boundary = headers.get("boundary")
            #boundary_bytes = received_data.split(b"boundary=")[1].split(b"\r\n")[0]
            boundary_bytes = boundary.encode("utf-8")
            current_part = b""
            last_boundary_found = False
            image_counter = 0

            #first parse headers
            content_length = headers.get("Content-Length")
            # split at '\r\n\r\n' to seperate the headers from the body
            received_data.split(b"\r\n\r\n")

            while(len(buffer) < int(content_length)):
                data = self.request.recv(2048)
                buffer += data
            
            if len(buffer) - int(content_length) > 0:
                remaining_data = buffer[int(content_length):]
                buffer = buffer[:int(content_length)]
                buffer += remaining_data

            parts = buffer.split(b"--" + boundary_bytes)[1:-1]
            for part_bytes in parts:
                if part_bytes.startswith(b"\r\n"):
                    part_bytes = part_bytes[2:]

                if part_bytes.endswith(b"\r\n"):
                    part_bytes = part_bytes[:-2]

                if part_bytes.endswith(b"--"):
                    part_bytes = part_bytes[:-2]
                    last_boundary_found = True

                if not current_part:
                    headers_end = part_bytes.find(b"\r\n\r\n") + 4
                    headers_bytes = part_bytes[:headers_end]
                    content_bytes = part_bytes[headers_end:]
                    current_part = content_bytes
                else:
                    current_part += part_bytes

                if last_boundary_found:
                # Extract the headers as a dictionary
                    headers_dict = {}
                    for header_line in headers_bytes.split(b"\r\n"):
                        if b":" in header_line:
                            key, value = header_line.split(b":", 1)
                            headers_dict[key.strip()] = value.strip()

                                # Check the name parameter in the headers to determine how to handle the content
                    name_param = headers_dict.get(b"Content-Disposition", "").split(";")[1].strip().split("=")[1].strip('"')
                    if name_param == b"upload":
                            image_filename = f"image{image_counter}.jpg"
                            image_counter += 1

                            # Read the following bytes until we hit the boundary
                            boundary_index = current_part.find(b"\r\n--" + boundary_bytes + b"\r\n")
                            file_bytes = current_part[:boundary_index-2]

                            # Remove the final '\r\n' bytes from the end of the file content
                            file_bytes = file_bytes[:-2]

                            # Save the file content to a file
                            with open(f"image/{image_filename}.jpg", "wb") as f:
                                f.write(file_bytes)

                            comments_collection.insert_one({"type": "file", "content": f"image/{image_filename}.jpg"})
                    elif name_param == b"comment":
                        # handle the following body as utf-8
                        comment_bytes = current_part[:-2]
                        comment_str = comment_bytes.decode('utf-8')

                        # Store the comment in the database
                        comments_collection.insert_one({"type": "comment", "content": comment_str})

                    current_part = b""
                    last_boundary_found = False
            
            # Redirect to the home page
            self.request.send('HTTP/1.1 303 See Other\r\nLocation: /\r\nContent-Length: 0\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n'.encode())

           # for data_bytes in iter(lambda: self.request.recv(buffer), b""):

            #    current_part += data_bytes

              #  while last_boundary_found == False:
                #    part, current_part = current_part.split(boundary_bytes, 1)
                  #  if part.endswith(b"--\r\n"):
                   #     last_boundary_found = True
                   # else:
                      #  pass
            #boundary_bytes = boundary.encode("utf-8")
            #if boundary:
                #buffer = buffer - 1
                #parts = self.data.split(("--" + boundary).encode("utf-8"))
       #     parts = body_bytes.split(b"--" + boundary_bytes)[1:-1]
       #     last_boundary = headers.get("boundary") + "--"
       #     last_boundary_bytes = last_boundary.encode("utf-8")
            #while buffer != 0:
               # for part_bytes in self.data:
                   # buffer = buffer-1
                # Check if the current part of the body starts with the boundary bytes
              #  if part_bytes.startswith(boundary_bytes):
              #      if part_bytes(boundary_bytes).endswith(b"--\r\n"):
              #          break
                    # Now we read the header of this section
                    # Find the start of the headers in this part of the body
                 #   headers_end = part_bytes.find(b"\r\n\r\n")
                 #   if headers_end != -1:
                        # The headers were found in this part of the body
                   #     headers_bytes = part_bytes[:headers_end+4]
                   #     content_bytes = part_bytes[headers_end+4:]

                         # Extract the headers as a dictionary
                    #    headers_dict = {}
                     #   for header_line in headers_bytes.split(b"\r\n"):
                     #       if b":" in header_line:
                     #           key, value = header_line.split(b":", 1)
                      #          headers_dict[key.strip()] = value.strip()
            
                        # Check the name parameter in the headers to determine how to handle the content
                     #   name_param = headers_dict.get(b"Content-Disposition", "").split(";")[1].strip().split("=")[1].strip('"')
                      #  if name_param == "upload":
                      #      image_filename = f"image{image_counter}.jpg"
                      #      image_counter += 1
                            # Read the following bytes until we hit the boundary
                      #      boundary_index = content_bytes.find(b"\r\n--" + boundary_bytes + b"--\r\n")
                            # Read the following bytes until we hit the boundary
                     #       if boundary_index != -1:
                      #          file_bytes = content_bytes[:boundary_index-2]
                                # Remove the final '\r\n\r\n' bytes from the end of the file content
                                #file_bytes = file_bytes[:-4]
                                # Save the file content to a file
                      #          with open(f"image/{image_filename}.jpg", "wb") as f:
                        #            f.write(file_bytes)
                                # Store the file in the database
                         #       comments_collection.insert_one({"type": "file", "content": "image/image_filename"})
                     #   elif name_param == "comment":
                      #      if boundary_index != -1:
                        #        file_bytes = content_bytes[:boundary_index-2]
                                # Remove the final '\r\n\r\n' bytes from the end of the file content
                                #file_bytes = file_bytes[:-4]
                                # Handle the following body as UTF-8
                       #         comment_bytes = content_bytes[:-4]
                       #         comment_str = comment_bytes.decode('utf-8')
                                # Store the comment in the database
                       #         comments_collection.insert_one({"type": "comment", "content": comment_str})

        else:
            self.request.send('HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n404 Not Found!'.encode())
    