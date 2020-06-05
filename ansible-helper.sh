#!/bin/sh
#
function print_usage () {
   echo "$0 file.yaml var1 var2 ..."
   exit 1
}

yaml_file=$1; shift
ansible_args=""

if [ -z "$yaml_file" ]
then
   print_usage
   exit 1
fi

for ARG in "$@"
do
    echo "$ARG"
done

for extra_var in $(cat $yaml_file | grep "^# var" | awk -F: '{print $2}')
do
  ansible_args=$(echo "${ansible_args}\"${extra_var}\":\"${1}\"")
  if [ $# -gt 1 ]
  then
     ansible_args=$(echo "${ansible_args},")
  fi
  shift
done

echo "Running playbook $yaml_file"
echo "Extra Vars $ansible_args"
echo -n "Continue? [y/n] "
read ANSWER
if [ "$ANSWER" != "y" ]
then
   exit 1
fi

/usr/bin/ansible-playbook $yaml_file --extra-vars "{${ansible_args}}"
