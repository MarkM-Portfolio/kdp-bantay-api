
   
#!/bin/bash
input="deployment.yaml"
unixtime=${1}
while IFS= read -r line
do
  if [[ $line == *"image:"* ]];
  then
    x="$line"
    echo -e "${x/${x##*:}/$unixtime}" >> new_deployment.yaml 
    line=$x
  else
    echo -e "$line" >> new_deployment.yaml 
  fi
done < "$input"

rm deployment.yaml
mv new_deployment.yaml  deployment.yaml 