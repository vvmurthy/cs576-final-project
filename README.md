# Preprocessing
```
python make_video_with_outputs.py dataset-001-001/dataset/Videos/data_test1.rgb dataset-001-001/dataset/Videos/data_test1.wav dataset-001-001/dataset/Videos/data_test_modified1.rgb dataset-001-001/dataset/Videos/data_test_modified1.wav
python make_video_with_outputs.py dataset-002-002/dataset2/Videos/data_test2.rgb dataset-002-002/dataset2/Videos/data_test2.wav dataset-002-002/dataset2/Videos/data_test_modified2.rgb dataset-002-002/dataset2/Videos/data_test_modified2.wav
python make_video_with_outputs.py dataset-003-003/dataset3/Videos/data_test3.rgb dataset-003-003/dataset3/Videos/data_test3.wav dataset-003-003/dataset3/Videos/data_test_modified3.rgb dataset-003-003/dataset3/Videos/data_test_modified3.wav
python make_video_with_outputs.py dataset-004-004/dataset4/Videos/data_test4.rgb dataset-004-004/dataset4/Videos/data_test4.wav dataset-004-004/dataset4/Videos/data_test_modified4.rgb dataset-004-004/dataset4/Videos/data_test_modified4.wav
```

# How to run
```
javac VideoGui.java
java -Xmx6G VideoGui dataset-001-001/dataset/Videos/data_test_modified1.rgb dataset-001-001/dataset/Videos/data_test_modified1.wav
java -Xmx6G VideoGui dataset-002-002/dataset2/Videos/data_test_modified2.rgb dataset-002-002/dataset2/Videos/data_test_modified2.wav
java -Xmx6G VideoGui dataset-003-003/dataset3/Videos/data_test_modified3.rgb dataset-003-003/dataset3/Videos/data_test_modified3.wav
java -Xmx6G VideoGui dataset-004-004/dataset4/Videos/data_test_modified4.rgb dataset-004-004/dataset4/Videos/data_test_modified4.wav
java -Xmx6G VideoGui dataset-004-004/dataset4/Videos/data_test4.rgb dataset-004-004/dataset4/Videos/data_test4.wav
```
