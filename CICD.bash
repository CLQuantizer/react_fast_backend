kill $(ps aux | grep '8000' | awk '{print $2}')
kill $(ps aux | grep '8001' | awk '{print $2}')
kill $(ps aux | grep '8002' | awk '{print $2}')
kill $(ps aux | grep '8003' | awk '{print $2}')

for dir in */; do
  (
    cd "$dir" || exit
    pwd
    poetry run bash run.bash
  )
done
