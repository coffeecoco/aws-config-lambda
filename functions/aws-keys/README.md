# aws-keys

This function flags users that have not rotated their access keys in a while
(by default 90 days).

The function also considers two active access keys to be a problem. The purpose
of having two keys is to safely be able to rotate them, not to use separate keys
on different machines. [Read the docs](http://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html).

Optional parameter:
- NumDays: Override the default 90 day period.
