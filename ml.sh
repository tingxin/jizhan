printf "begin\n"
printf "process\n"
echo "Script name is : $0"
echo "The 1st parameter is : $1"
echo "The 2nd parameter is : $2"
echo "The 3rd parameter is : $3"

cp /home/ec2-user/work/jizhan/resource/body_black_55_45cm.glb /home/ec2-user/work/jizhan/work/temp/
mv /home/ec2-user/work/jizhan/work/temp/body_black_55_45cm.glb /home/ec2-user/work/jizhan/work/temp/final3c2.glb
sleep 5
printf "done\n"