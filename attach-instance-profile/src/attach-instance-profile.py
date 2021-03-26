import boto3
import time 
ec2 = boto3.client('ec2')

def replace_iam_instance_profile_association (attach_profile_arn, current_association_id):
    print("Disassociating {}".format(current_association_id))
    disassociated = ec2.disassociate_iam_instance_profile(
        AssociationId=current_association_id
    ).get('IamInstanceProfileAssociation', {})  
    instance_id = disassociated.get('InstanceId', '')
    state = disassociated.get('State', 'disassociated')
    if state != 'disassociated': 
        time.sleep(30)
    print("Attaching {} to {}".format(attach_profile_arn, instance_id))
    return ec2.associate_iam_instance_profile(
        IamInstanceProfile={'Arn': attach_profile_arn},
        InstanceId=instance_id                     
    )    

def script_handler (events, context):
    instance_id = events["InstanceId"]
    attach_profile_arn = events["AttachInstanceProfileArn"]
    force_replace = True if events.get("ForceReplace", "False").strip().lower() == "true" else False
    override_profiles_list = events.get("OverrideProfileList", "").split(",")
    print ("InstanceId: {}".format(instance_id))
    print ("AttachInstanceProfileArn: {}".format(attach_profile_arn))
    print ("ForceReplace: {}".format(force_replace))
    print ("OverrideProfileList: {}".format(",".join(override_profiles_list)))

    current_association = ec2.describe_iam_instance_profile_associations(
        Filters=[
            {
                'Name': 'instance-id',
                'Values': [instance_id]
            },
        ]
    ).get('IamInstanceProfileAssociations', [])
    current_association = current_association[0] if len(current_association) else {}
    current_association_id = current_association.get('AssociationId', '')
    current_association_profile_arn = current_association.get('IamInstanceProfile', {}).get('Arn', '')
    
    if not current_association:
        print("No instance profile attached, assigning.")
        ec2.associate_iam_instance_profile(
            IamInstanceProfile={'Arn': attach_profile_arn},
            InstanceId=instance_id                     
        )
        return "Attached: {}".format(attach_profile_arn)
    elif force_replace:
        print("Forcing replacement: Association {} profile {}".format(current_association_id, current_association_profile_arn))
        replace_iam_instance_profile_association(attach_profile_arn, current_association_id)  
        return "Forcefully Replaced: {}". format(attach_profile_arn)
    else:    
        current_profile_name = current_association_profile_arn.rsplit('/',2)[1].strip()
        for profile in override_profiles_list:
            if current_profile_name.strip().lower() == profile.strip().lower():
                print("Overriding: Association {} profile {} with {}".format(current_association_id, current_profile_name, attach_profile_arn))
                replace_iam_instance_profile_association(attach_profile_arn, current_association_id)
                return "Overridden: Association {} profile {} with {}".format(current_association_id, current_profile_name, attach_profile_arn)
        print("Skipped: Existing profile {} already attached".format(current_profile_name))
        return "Skipped: Existing profile {} already attached".format(current_profile_name)
