'''
The following is an annotated version of the code (https://github.com/char/blm-instagram-bot) to teach 
students about using python in socially critical projects that can support a social cause

With char's permission(@blastbots on twitter and char on github)
Annotated by Jason Li for Parsons Summer Python Course 2020
'''

'''-------------------------------------
First Code Block: Declaring Libraries

This is where library imports are made. Because python projects can make use of other libraries, it makes
sense to simply import those pieces of code where you can. Some are highly specific, like the instagram api,
while some are more generic, like os or randint. Either way, these are useful for encapsulating the code that 
we are working with in a given code file.
-------------------------------------'''

#https://github.com/ping/instagram_private_api
#https://instagram-private-api.readthedocs.io/en/latest/api.html#instagram_private_api.Client
#Lets us use instagram from python
from instagram_private_api import Client, ClientCompatPatch

#https://pypi.org/project/python-dotenv/
#Lets us use virtual environments for scope control
from dotenv import load_dotenv, find_dotenv

#https://docs.python.org/3/library/json.html
#:ets us use the json format and translate it to dictionary and list forms
import json

#https://pypi.org/project/requests/
#Lets us access the internet
import requests

#https://docs.python.org/3/library/os.html
#Lets us access Operating System details
import os

#https://docs.python.org/2/library/time.html
#Lets us access time related variables and specifically "sleep" functions
from time import sleep

#https://docs.python.org/3/library/random.html
#Lets us use random number generation, specifically random integers
from random import randint

#https://github.com/CodeForeverAndEver/ColorIt
#A library to make colored terminal output
#Any print statement that ends in colors.YELLOW or colors.RED is using this library
from ColorIt import *

#https://docs.python.org/3/library/ssl.html
#A library to make sure our internet connection is secure
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

#https://github.com/RazerM
#A library to limit our running speed
from ratelimiter import RateLimiter


'''-------------------------------------
Second Code Block - Globally Named Variables

Here we decide what variables we are going to be using throughout this portion of the code.
We declare 3 lists, a boolean, load an environment (for isolating this bot) and initialize the Color library (the initColorIt)
-------------------------------------'''

#RateLimiter is a library that allows us to make repeated calls of a function
rate_limiter = RateLimiter(max_calls=1, period=5.0);

#The clients list holds the instance of our instagram session, or several, because it is a list
clients = []

#Feed holds the posts in a feed. 
feed = []

#This will be the confirmation of whether or not our current post has a comment already
contains_comment = False

#This is the set of comments we will post onto a post that meets the criteria
comments = [
    'Hi, please dont use the blacklivesmatter tag as it is currently blocking important info from being shared. Please delete and repost with #BlackoutTuesday instead (Editing the caption wont work). If you want other ways to help please check out our bio. Thank you :)',
    'Please use the #blackouttuesday instead of blacklivesmatter if you''re posting a black square.  Please delete and repost with #BlackoutTuesday instead (Editing the caption wont work). If you want other ways to help please check out our bio. Thank you :)',
    'It appears you have posted a black square in the wrong hashtag blacklivesmatter is used to spread critical information. Please delete and repost with #BlackoutTuesday instead (Editing the caption wont work). If you want other ways to help please check out our bio. Thank you :)',
    'Posting black screens is hiding critical information please delete your image and repost it with the #BlackoutTuesday instead. If you want other ways to help please check out our bio. Thank you :)'
]

'''-------------------------------------
Third Code Block - The work

Now we are actually where we do the work. This script follows this sequence
1. Access the instagram account we are using
2. Get the search feed of all the posts that have #blacklivesmatter
3. Check if those pictures have an image that is a blackouttuesday 
4. If we find one of those pictures,
    respond kindly, telling them that posting into the #blacklivesmatter tag is clogging and blocking
5. Move onto the next photo
6. Repeat 3-5 until we are finished, or Instagram's post limit stops us

All sections have been marked with the number that matches them.
-------------------------------------'''
#This is to load an environment to keep this boy instance separate from others
load_dotenv(find_dotenv())

#this colors our console output. Does not interface with the instagram side at all
initColorIt()


'''STEP 1'''
#login to instagram

#using the account.json file that has the username and password:
with open('./accounts.json') as f:
    #prepare a JSON object
    data = json.load(f) 
    #go through that JSON object, for however many accounts we have
    for acc in data:
        #Confirm in the terminal that we're logging in
        print('Logging in with username %s' % acc['username'] + '\n')

        #Tell the instagram client to log in with the username and password
        #Add the client to the clients list
        #Get the blacklivesmatter feed 
        client = Client(acc['username'], acc['password'])
        clients.append(client)
        
        '''STEP 2'''
        feed = client.feed_tag('blacklivesmatter', client.generate_uuid())



'''STEP 3'''
#So while we have the images in the feed, we will now loop over them as long as there are photos
#Goes over the pictures in the black lives matter hashtag
while len(feed) != 0:
    #for every account that we are using, do the following code
    for client in clients:
        #Do the following at the speed of the rate limiter:
        with rate_limiter:

            #Log into the terminal that we are beginning the process
            #This is the start of the image search
            print ('Looking for an image... \n')
            #.pop() gets the last item in the list and removes the item at the same time
            #it draws a card off the top of the list
            #post is going to reference that item that we remove
            post = feed['items'].pop(0)     
            #This logs that we found a certain amount of images   
            print ('Found ' + str(feed['num_results']) + ' images. \n')

            #This is a random wait timer. Probably to avoid spam filters
            #It picks a random integer, from the random library above, and then 
            #sleep makes it hang for an amount of time
            waitTime = randint(10,30)
            print(color('Waiting ' + str(waitTime) + ' sec. \n',colors.YELLOW))
            sleep(waitTime)

            #This tells us that we are "analyzing"
            print ('Analyzing post '+ post['code'] +' ...\n')

            #At this point, we are logged into the account via the API, and we use the API to get all the 
            #latest posts. Then we start looking through them.
            #image_versions2 is instagram convention for how to reference the posts
            if 'image_versions2' in post:
                #this is an error handling piece. try: is paired with except: to do error checking
                try:
                    '''
                    
                    STEP 3
                    
                    First we navigates the post's data structure to get the url of the image itself
                    Remember that we already are looking at only images with the blacklivesmatter hashtag
                    And we are searching specifically for the solid image

                    This line of code accesses the internet using the environment in the Dockerfile
                    To send the image to a different API at https://us-central1-protect-blm.cloudfunctions.net/isSolidColor
                    This returns the details of the image and stores it in res, then creates a JSON of it referenced in json_res
                    
                    The scope of Docker is not covered for this class, but it is an online hosting system for automizations
                    Happens to be useful if we need to process an image quickly, like in this situation. https://docs.docker.com/get-started/
                    '''
                    
                    url = post['image_versions2']['candidates'][0]['url']
                    res = requests.post(os.getenv("CLOUD_FUNCTION_URL"), data = { 'img_url': url })
                    json_res = res.json()

                    '''Then we do a series of checks based on that image to make sure that we do not double post.'''
                    # check if the image is a black square
                    if(json_res['solid']):
                        #Again, anything in the post[] format is something that is stored by Instagram.
                        code = post['code']

                        #Check if the comments are disabled! Some people don't want people to comment
                        if 'comments_disabled' in post:
                            #Woops can't comment, but this terminal print reports that back
                            print('Bot cannot comment on post due to disabled comments: %s' % code)
                            continue #continue tells the loop to start over at the while statement above.
                        #Check if the post has a set of comments yet
                        if 'comment_count' in post and post['comment_count'] > 0:
                            #This makes sure that we didn't comment already!
                            #This for loop checks every comment on a post.
                            for comment in post['preview_comments']:
                                #And we compare if any of the comments have this line from our own comments contained in the post
                                if "If you want other ways to help please check out our bio. Thank you :)" in comment['text'].lower():
                                    #Then we know the post contains the comment and we set it to true
                                    contains_comment = True
                                    continue
                            
                            '''STEP 4''''
                            #And now we know we haven't commented yet so we comment!
                            if not contains_comment:
                                #Log that we found an image in the terminal
                                print(color('Solid image found. Informing user on post %s' % code + '\n',colors.ORANGE))
                                #Randomly pick a comment from our 4 available options
                                randomlySelectedComment = randint(0,3)
                                #Tell the instagram API to post the comment
                                client.post_comment(post['id'], str(comments[randomlySelectedComment]))
                                #Log in Terminal that we commented
                                print(color('commented successfully. \n',colors.GREEN))
                            #If we found our comment in the post
                            else:
                                #Log that we found that comment in the terminal
                                print('Bot has already commented on post: %s' % code)
                                #Set the variable to false because the next post will start over
                                contains_comment = False
                        #If the post has no comments, then it's easy to know if we've posted. We haven't... because there's no comments
                        else:
                                #Log into console that we found an image and are commenting
                                print(color('Solid image found. Informing user on post %s' % code + '\n',colors.ORANGE))
                                #Randomly pick a comment from our 4 available options
                                randomlySelectedComment = randint(0,3)
                                #Tell the instagram API to post the comment
                                client.post_comment(post['id'], str(comments[randomlySelectedComment]))
                                #Log in Terminal that we commented
                                print(color('commented successfully. \n',colors.GREEN))
                    #We didn't find a black square on this image so we move on
                    else: 
                        print('Image isn''t a black square.. moving on the next..')
                #Some where in the commenting business, we got a runtime error or a syntax error
                #We keep that Exception (python gives this to us in a try block), and store it in e
                '''Step 6 is contained technically in this exception handling'''
                except Exception as e:
                    #Instagram will give us the error data and it might tell us we are spamming the comments
                    if 'spam": true,' in e.error_response:
                        #Then we log that in the terminal
                        print(color("Error : Commented too many times. \n", colors.RED))
                    #It wasn't a spam error so it was something else
                    else:
                        #we print that error here in the terminal
                        #repr() is a way of making sure string comes back in a quotes appended format
                        #https://docs.python.org/3.8/library/functions.html#repr
                        print(color(repr(e) +'\n', colors.RED))
                    continue

            '''Step 5'''
            #This loops again as it moves down the feed.
            #If we only have one item left in the feed
            if len(feed) == 1:
                #Refresh the feed with the client instagram API
                feed = client.feed_tag('blacklivesmatter', client.generate_uuid())

        

