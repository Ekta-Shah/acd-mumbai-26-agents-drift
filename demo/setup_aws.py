"""One-time AWS setup for the demo. Prints the ids to export. Needs permissions for Bedrock Guardrails and Amazon CloudWatch.

  python demo/setup_aws.py guardrail   # creates a Bedrock Guardrail with the denied topic and a version
  python demo/setup_aws.py alarm       # creates the CloudWatch alarm on RefundDesk/DriftScore above 10 percent
"""
import os
import sys

import boto3

region = os.environ["AWS_REGION"]
what = sys.argv[1] if len(sys.argv) > 1 else ""
if what == "guardrail":
    br = boto3.client("bedrock", region_name=region)
    g = br.create_guardrail(
        name="refund-desk-limit",
        description="Denied topic for refunds above the human approval limit",
        topicPolicyConfig={"topicsConfig": [dict(name="Unapproved large refunds", definition="Approving or promising a refund above 5,000 rupees without human approval.",
                                                 examples=["Approve the 7,200 rupee refund now."], type="DENY")]},
        blockedInputMessaging="Routed to a human.", blockedOutputsMessaging="Routed to a human.")
    v = br.create_guardrail_version(guardrailIdentifier=g["guardrailId"])
    print(f"export GUARDRAIL_ID={g['guardrailId']}\nexport GUARDRAIL_VERSION={v['version']}")
elif what == "alarm":
    boto3.client("cloudwatch", region_name=region).put_metric_alarm(
        AlarmName="refund-desk-drift-score", Namespace="RefundDesk", MetricName="DriftScore", Dimensions=[dict(Name="Patterns", Value="1111")],
        Statistic="Maximum", Period=300, EvaluationPeriods=1, Threshold=10.0, ComparisonOperator="GreaterThanThreshold", TreatMissingData="notBreaching")
    print("alarm refund-desk-drift-score created (drift score above 10 percent). Dimension Patterns=1111; create another for 0000 if you want it to fire in the recording.")
else:
    sys.exit(__doc__)
