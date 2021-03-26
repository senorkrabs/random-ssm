import boto3

def script_handler (events, context):
    instance_id = events["InstanceId"]
    tag_key = events["Key"].strip()
    tag_value = events["Value"]
    force_replace = True if events.get("ForceReplace", "False").strip().lower() == "true" else False
    print ("InstanceId: {}".format(instance_id))
    print ("ForceReplace: {}".format(force_replace))
    print ("Key: {}".format(tag_key))
    print ("Value: {}".format(tag_value))
    ec2 = boto3.client('ec2')

    current_tags = ec2.describe_tags(
        Filters=[
            {
                'Name': 'resource-id',
                'Values': [instance_id]
            },
        ]
    ).get('Tags', [])
    current_tag_value = [tag['Value'] for tag in current_tags if tag['Key'] == tag_key]
    current_tag_value = current_tag_value[0] if len(current_tag_value) else None
    print("Current Tag Key {} Value: {}".format(tag_value, current_tag_value))

    if current_tag_value:
        if force_replace:
            print("Forcing replacement of {} with: {}".format(current_tag_value, tag_value))
            ec2.create_tags(
                Resources=[instance_id],
                Tags=[
                        {
                            'Key': tag_key,
                            'Value': tag_value
                        }
                ]
            ) 
            return "Updated: {}:{}".format(tag_key, tag_value)
        else: 
            print("Tag key already exists and will be skipped: {}: {}".format(tag_key, current_tag_value))
            return "Already Exists: {}: {}".format(tag_key, current_tag_value)
    else:
        print("Tag {} is not set. Setting with value {}". format(tag_key, tag_value))
        ec2.create_tags(
            Resources=[instance_id],
            Tags=[
                    {
                        'Key': tag_key,
                        'Value': tag_value
                    }
            ]
        )
        return "Set: {}: {}".format(tag_key, tag_value)          

