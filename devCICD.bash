kill $(ps aux | grep "uvicorn datapanel" | awk '{print $2}')
kill $(ps aux | grep "uvicorn glove" | awk '{print $2}')
kill $(ps aux | grep "uvicorn journal" | awk '{print $2}')
kill $(ps aux | grep "uvicorn infra" | awk '{print $2}')
kill $(ps aux | grep "celery -A tasks worker" | awk '{print $2}')

for dir in */; do
  (
    cd "$dir" || exit
    if [[ "$dir" == *infra/ ]]
    then
      poetry run celery -A tasks worker --loglevel=INFO &
    fi
    poetry run bash dev.bash
  )
done
