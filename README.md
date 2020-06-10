# ansible-playbooks
Ansible Playbooks and NetApp Ansible Samples

The ansible helper allows you to run a playbook and pass in variables on the command line. This can be done directly with ansible-playbook and the Extra Vars option, but this program makes this process more user friendly. You define the external variables in specially crafted comments (# var:var_name). You can then pass these via long style arguments as --var_name. If you combine this with "if defined else" variable constructs you can set default values and pass only the needed variables through the helper program. 

````
$ mkdir $HOME/playbooks
$ cd playbooks
$ git clone mminichino/ansible-playbooks
$ ./ansible-helper.py mount_ontap_nfs_share.yaml --cluster_admin_ip w.x.y.z --vol_aggregate aggr1 --vol_size 100 --svm_name svm0 --nfs_lif w.x.y.z --mount_point /u01 --mount_owner oracle --mount_group dba --vol_name orabin --host_group database
````
