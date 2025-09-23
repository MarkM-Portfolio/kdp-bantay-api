
from . import bantay_api
from flask import current_app
from flask import request
from app.extensions import awslambda
from kumuniverse.malacanang_api import MalacanangAPI
from kumuniverse.logger import Logger
from requests_aws4auth import AWS4Auth
import requests
import json   
import os
import concurrent
import concurrent.futures
import datetime
import uuid


logger = Logger(name="Bantay", env=os.environ.get("ENV"))




def slack_alerts( channel, sqs_message, slack_message):
   
        """
        Triggers the Lambda function slack_alerts for sending sqs and slack messages
        Args:
            sqs_message: dictionary. contains the sqs message
            slack_message: string. contains the slack message
        """
        lambda_client = awslambda.client
        lambda_name = awslambda.name
      
        data = {
            "channel": channel,
            "sqs_message": sqs_message,
            "slack_message": slack_message,
        }

        try:
            res = lambda_client.invoke(
            FunctionName=lambda_name, InvocationType="Event", Payload=json.dumps(data) 
        )
        except:
            logger.error(msg = f"Error in {lambda_name}")
            pass

        return res

def call_model_endpoint(url_val,content,aws_access_id,aws_access_key,aws_region):
    
    data = {
            "image_url": content
        }
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    try:
        
        r = requests.post(url=url_val, headers=headers,  auth=AWS4Auth(aws_access_id, aws_access_key, aws_region, "sagemaker"), json=data)
       
        return r.text
    except Exception as err:
        logger.error(msg="Call Model Error:" + str(err))
        
        raise Exception(
            err
        )
        

def use_threading(URLS,content,admin_url):
    data = []
    prediction_id = ""
    prediction_timestamp = ""

    aws_access_id = current_app.config["AWS_ACCESS_KEY_ID"]
    aws_access_key = current_app.config["AWS_SECRET_ACCESS_KEY"]
    aws_region = current_app.config["AWS_REGION"]


   
    
    #Call endpoints with threading
    errorLogs = []
    with concurrent.futures.ThreadPoolExecutor(
                max_workers= len(URLS)
            ) as executor:
                futures = [
                    executor.submit(call_model_endpoint, url,content,aws_access_id,aws_access_key,aws_region)
                    for url in URLS
                ]
                for future in concurrent.futures.as_completed(futures):
                    if future.exception() is not None:
                        errorLogs.append(future.exception()) 
                        pass
                    else:
                        try:

                            dict_result = json.loads(future.result())
                            if "ErrorCode" in dict_result:
                            
                                errorLogs.append(dict_result["Message"]) 
                                pass

                            #get the model result in the data
                            model_readings = dict_result["data"]
                          
                            for readings in model_readings:
                                data.append({ "category":readings["category"], "probability":round(readings["probability"],2) })
                           
                        except Exception as e:
                            pass

    
    #check if there is at least 1 model that was called successfully                   
    if not data:
        #if there are no model results, and there is an error
        if errorLogs:
            return {"ModelErrors":errorLogs}
        else:
            return []
    else:
        #log 1 model error if there is any
        if errorLogs:
            logger.error(msg = {"ModelErrors":errorLogs})


        #return clean results, generate id and timestamp
        filename = content.split("/")[-1].split(".")[0]
        current_timestamp = datetime.datetime.now()
        prediction_timestamp = current_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        prediction_id = f"{filename}-{str(uuid.uuid4())}"
        return {"data":data,"prediction_id":prediction_id,"prediction_timestamp":prediction_timestamp}


def aggregate_violations(not_safe, category, content,admin_url,timestamp,id,photo_type,abs_model_categories,safe):

    
    channel = None
    slack_message = None
    sqs_data = []
    sqs_message = ""
    category_average_probability = 0

    
    
    #set slack channel - change if Live
    if category == "nude": 
        filtered_by_category = [x for x in not_safe if x['category']==category]
   
        category_average_probability =  round(sum(map(lambda x: x["probability"], filtered_by_category)) / len(filtered_by_category),2)
        slack_message = f"Bantay - {category.capitalize()} {photo_type} detected!\nLink to Actual Photo(NSFW): {content}\nProbability: {str(category_average_probability)}\nLink to Admin Tool: {str(admin_url)}"
        sqs_data.append({"category":category,"probability":category_average_probability})
        channel = awslambda.moderation_channel

       
    elif category == "nonperson":
        filtered_by_category = [x for x in not_safe if x['category']==category]
   
        category_average_probability =  round(sum(map(lambda x: x["probability"], filtered_by_category)) / len(filtered_by_category),2)
        slack_message = f"Bantay - {category.capitalize()} {photo_type} detected!\nLink to Actual Photo(NSFW): {content}\nProbability: {str(category_average_probability)}\nLink to Admin Tool: {str(admin_url)}"
        sqs_data.append({"category":category,"probability":category_average_probability})
        channel = awslambda.nonperson_channel

        
        
    else:
        #nonperson with other violations, overwrite sqs data to include nonperson probability
        channel = awslambda.nonperson_channel
       
        #get the nonperson probability as well and append it to the sqs_data
        non_person_data = [x for x in not_safe if x['category']=="nonperson"]  
        category_message = ""
        probability_message = ""
        abs_model_probability = []
       
        
        cnt = 0
        cnt_other = 0
        for other_category in abs_model_categories:
            filtered_by_category = [x for x in not_safe if x['category']==other_category]
            category_average_probability =  round(sum(map(lambda x: x["probability"], filtered_by_category)) / len(filtered_by_category),2)
            abs_model_probability.append(category_average_probability)

            if photo_type == "Timeline Photo" :
                if (other_category == "weapon" or other_category == "wine" or other_category == "pistol" or other_category == "cigarette"):
                    if cnt_other > 0:
                        category_message += "/"
                        probability_message += "/"
                    category_message += other_category.capitalize()
                    probability_message += str(category_average_probability)
                    cnt_other += 1
            else:
                #as is logic
                if cnt > 0:
                    category_message += "/"
                    probability_message += "/"
                category_message += other_category.capitalize()
                probability_message += str(category_average_probability)
                cnt+=1

            sqs_data.append({"category":other_category,"probability":category_average_probability})
        
        #no slack alerts, its a timeline photo with no violation
        if category_message == "":
            slack_message = ""
            channel = ""
        else:
            slack_message = f"Bantay - Nonperson - {category_message} {photo_type} detected!\nLink to Actual Photo(NSFW): {content}\nProbability: {probability_message}\nLink to Admin Tool: {str(admin_url)}"
        
        
        #add nonperson to sqs message if there is any
        if len(non_person_data) > 0:
            sqs_data.append(non_person_data[0])
            abs_model_categories.append("nonperson")
            abs_model_probability.append(non_person_data[0]["probability"])
            
         #add safe to sqs message if there is any
        if len(safe) > 0:
            sqs_data.append(safe[0])
            abs_model_categories.append("safe")
            abs_model_probability.append(safe[0]["probability"])

        sqs_message = {
            "model_id": awslambda.sqs_model_id+"-"+photo_type,
            "invoked_production_variant": "NULL",
            "image_url": content,
            "admin_url": admin_url,
            "data": sqs_data,
            "category": abs_model_categories,
            "probability": abs_model_probability,
            "timestamp":timestamp,
            "prediction_id":id
        }   
    
    if category != "other":
        sqs_message = {
            "model_id": awslambda.sqs_model_id+"-"+photo_type,
            "invoked_production_variant": "NULL",
            "image_url": content,
            "admin_url": admin_url,
            "data": sqs_data,
            "category": category,
            "probability": category_average_probability,
            "timestamp":timestamp,
            "prediction_id":id
        }

    #no slack alerts for timeline photo, only
    if photo_type == "Timeline Photo":
        #for nude
        if category == "nude" or category == "other":
            slack_alerts(channel, sqs_message, slack_message)
        else:
            # no alerts for nonperson
            slack_alerts("", sqs_message, "")
    else:
        slack_alerts(channel, sqs_message, slack_message)


def slack_alerting_logic(final_results, content, admin_url,flag,photo_type):

    if flag == "end":
        return "gg"
    else:
        #check results for slack message filtering
        #get all unsafe
        not_safe = [x for x in final_results["data"] if x['category'] != 'safe']  

       
        #check if all safe no slack alerts needed
        if len(not_safe) == 0:
            #all are safe
            average_probability =  round(sum(map(lambda x: x["probability"], final_results["data"])) / len(final_results["data"]),2)
            sqs_message = {
                "model_id": awslambda.sqs_model_id+"-"+photo_type,
                "invoked_production_variant": "NULL",
                "image_url": content,
                "admin_url": admin_url,
                "data":[{"category":"safe","probability":average_probability}],
                "category": "safe",
                "probability": average_probability,
                "timestamp": final_results["prediction_timestamp"],
                "prediction_id": final_results["prediction_id"]
            }
            #safe - no slack alerts needed, only sqs
            slack_alerts("", sqs_message, "")

        else:
            #get all the unique categories returned by result without safe, 
            unique_categories = set(list(map(lambda x: x["category"] , not_safe)))

            #check for safe, this will be added to the sqs message
            safe = [x for x in final_results["data"] if x['category'] == 'safe']  
            # possbile unique violations: [nude,weapon], [nonperson,weapon], [weapon] , [nonperson],
            # remove the nonperson in category, if there are still remaining items, (can be [nude,weapon] or [weapon only])   
            # if nothing remains, violation is only nonperson so send only to nonperson as is without any additional violation


            filter_nonperson_violation = [x for x in unique_categories if x != 'nonperson']
            if len(filter_nonperson_violation) > 0:
                #there are other violations, can be nude and/or weapon/alcohol/mask
                unique_categories = filter_nonperson_violation

            #check if there are other nonperson category (weapon, mask)
            abs_model_categories = [i for i in unique_categories if i  != "nude" and i  != "nonperson"]
            if len(abs_model_categories) > 0:
                #remove from unique categories, to be consolidated later
                unique_categories = [x for x in unique_categories if x not in abs_model_categories]
                unique_categories.append("other")


            #Call endpoints with threading
            timestamp = final_results["prediction_timestamp"]
            id = final_results["prediction_id"]
            with concurrent.futures.ThreadPoolExecutor(
                        max_workers= len(unique_categories)
                    ) as executor:
                        futures = [
                            executor.submit(aggregate_violations, not_safe, category, content,admin_url,timestamp, id,photo_type,abs_model_categories,safe)
                            for category in unique_categories
                        ]
                        for future in concurrent.futures.as_completed(futures):
                            if future.exception() is not None:
                                pass 
            return "awit"



    
@bantay_api.route("/photo_moderation", methods=["POST"])
def photo_moderation():
    
    if request.method == "POST":
        input = request.json

        content = input["content"]
        admin_url = input["admin_url"]
        photo_type = input["type"]
        #for the source of photo
        if photo_type == "image":
            photo_type = "Timeline Photo"
        elif photo_type == "cover-photo":
            photo_type = "Cover Photo"
        else:
            return {
                "status":400,
                "error":"Type is invalid",
            }, 400
        #input validation
        if not content or not admin_url or not photo_type :
            return {
                "status":400,
                "error":"Input is invalid ",
            }, 400
            

        #process input before calling malacanang
        #user_id photo_url/<content url>
        body = {
            "type": "content",
            "content_id":"photo/"+content,
            "use_case":"photo_moderation"
        }
        
        ## Call Malacanang API 
        if current_app.config["ENVIRONMENT"] != "DEV":
            #force to dev for now
            #malacanang_api = MalacanangAPI(env="dev")
            malacanang_api = MalacanangAPI(env="live")
        else:
           malacanang_api = MalacanangAPI(env="dev")
        URLS = []
        try:
            variant = malacanang_api.get_variant(body)
            if "rollout_variants" in variant:
                URLS = variant["rollout_variants"][0]["properties"]["urls"]
              
            else:
                URLS = variant["properties"]["urls"]
            
            
        except Exception as e:
            logger.error(msg = "Error calling Malacanang:")
            return {
                "status":400,
                "error":"Error calling Malacanang Endpoint",
            }, 400
        

        #use threading to access model endpoint
        final_results = use_threading(URLS,content,admin_url)

        #no valid results from models, and errors were thrown, final results has the error logs
        if "ModelErrors" in final_results:
            logger.error(msg = final_results)
            return {
                "status":400,   
                "error":"Error calling all models Endpoints",
            }, 400
        
        #no readings from the models, no errors were thrown
        if not final_results:
            return {
               "status":400,   
               "error":"Error calling all models Endpoints",
           }, 400



        #use THREAD TO CALL Backend AND SLACK alerts
        flags = ["","end"]
        with concurrent.futures.ThreadPoolExecutor(
                        max_workers= 2
                    ) as executor:
                        futures = [
                            executor.submit(slack_alerting_logic,final_results, content, admin_url,flag,photo_type)
                            for flag in flags
                        ]
                        for future in concurrent.futures.as_completed(futures):
                            if future.exception() is not None:
                                pass
                            else:
                               if future.result() == "gg":
                                   return final_results
    else:
        pass

