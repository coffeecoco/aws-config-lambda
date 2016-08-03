# idle-ebs

This function tries to help you save money by not letting unused EBS volumes
lie around.

It flags unattached volumes ("available") and volumes that are associated with
stopped instances. If you have an instance that is stopped most of the time,
you can consider creating a snapshot/AMI and use that to recreate your instance
whenever you need it.

According to [the pricing page](https://aws.amazon.com/ebs/pricing/):
> Snapshot storage is based on the amount of space your data consumes in Amazon S3. Because data is compressed before being saved to Amazon S3, and Amazon EBS does not save empty blocks, it is likely that the snapshot size will be considerably less than your volume size. For the first snapshot of a volume, Amazon EBS saves a full copy of your data to Amazon S3. For each incremental snapshot, only the changed part of your Amazon EBS volume is saved.

This means that if you snapshot a large volume that has mostly empty blocks,
you will pay considerably less than letting the EBS volume be idle.

Example:
- 500 GB of gp2 costs $50 / month
- if you use 10% of that volume and snapshot it, then you would pay less than $5 / month

Optional parameter:
- MinSize: Do not evaluate EBS volume if it's not this many GB.

More information:
- https://forums.aws.amazon.com/thread.jspa?threadID=169566
