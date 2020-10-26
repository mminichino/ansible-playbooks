# ansible-playbooks
Ansible Playbooks and NetApp Ansible Samples

The ansible helper allows you to run a playbook and pass in variables on the command line. This can be done directly with ansible-playbook and the Extra Vars option, but this program makes this process more user friendly. You define the external variables in specially crafted comments (# var:var_name). You can then pass these via long style arguments as --var_name. If you combine this with "if defined else" variable constructs you can set default values and pass only the needed variables through the helper program. 

````
$ mkdir $HOME/playbooks
$ cd playbooks
$ git clone mminichino/ansible-playbooks
$ ./ansible-helper.py mount_ontap_nfs_share.yaml --cluster_admin_ip w.x.y.z --vol_aggregate aggr1 --vol_size 100 --svm_name svm0 --nfs_lif w.x.y.z --mount_point /u01 --mount_owner oracle --mount_group dba --vol_name orabin --host_group database
````

To see supported variables, use the print option:

````
$ ./ansible-helper.py mount_ontap_nfs_share.yaml -p
--cluster_admin_ip
--vol_aggregate
--vol_name
--vol_size
--export_policy
--svm_name
--mount_point
--mount_owner
--mount_group
--nfs_lif
--nfs_options
--host_group
````

To see verbose Ansible output, use the -d option, and to do a dry run use the -c option.

You can save variable values to quickly replay a scenario with a specific playbook. You will be prompted for each parameter, and you can enter a value for that parameter that will be saved. Just hit enter if you don't want to save a value for that parameter. You will also be asked if you want to be prompted on replay to edit the saved value. If you select "y" then before the scenario is replayed, you will have a chance to edit that parameter.

````
$ ./ansible-helper.py ontap_incr_merge_clone.yaml -s testdb_copy
````

To replay a scenario that was previously saved:

````
$ ./ansible-helper.py ontap_incr_merge_clone.yaml -r testdb_copy
````
