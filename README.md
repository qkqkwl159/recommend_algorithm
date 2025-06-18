# Recommend_algorithm _ 동영상 추천 알고리즘

# Description

영상의 전체시간 / 시청시간 비율로 각 카테고리의 영상비율을 평균값으로 하여 점수가 가장높은 카테고리의 영상을 다음에 시청할때 우선으로 리스트 업 함

# Test

실행할 영상파일이 부족할 경우 ```dummy_gen.py```를 실행하여 15초 dummy 영상 생성가능 

```shell
python3 dummy_gen.py
```

# Excute

영상이 있는 디렉터리 경로로 설정하여 영상 카테고리 분류와 파일의 데이터 베이스를 저장 

```shell
python3 make_video_db file_path/eg/
```

datainfo 디렉터리에 ```video_db.csv```가 생성된걸 확인후 아래 실행

```shell
python3 watch_emul.py
```

