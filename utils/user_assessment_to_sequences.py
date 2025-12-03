import pandas as pd
import numpy as np


student_assessment = pd.read_csv('data/open_uni/studentAssessment.csv')
assessments = pd.read_csv('data/open_uni/assessments.csv')
student_info = pd.read_csv('data/open_uni/studentInfo.csv')

student_info = student_info.dropna(subset=['id_student','final_result'])
student_assessment = student_assessment.dropna(subset=['id_student','score','id_assessment'])

student_assessment = student_assessment.merge(
    assessments[['id_assessment','assessment_type', 'code_module','code_presentation']],
    on='id_assessment',
    how='left'
)

student_assessment = student_assessment.dropna(subset=['assessment_type'])

def score_bin(score):
    try:
        score = float(score)
    except:
        return 'missing'
    if score < 50:
        return 'fail'
    elif score < 70:
        return 'low'
    elif score < 85:
        return 'medium'
    else:
        return 'high'

student_assessment['score_bin'] = student_assessment['score'].apply(score_bin)

student_assessment['event'] = (
    student_assessment['assessment_type'] + '_' +
    student_assessment['id_assessment'].astype(str) + '_' +
    student_assessment['score_bin']
)

student_assessment['date_submitted'] = pd.to_numeric(student_assessment['date_submitted'], errors='coerce')
student_assessment = student_assessment.dropna(subset=['date_submitted'])
student_assessment.sort_values(['id_student','date_submitted'], inplace=True)

sequences_df = student_assessment.groupby('id_student')['event'].apply(list).reset_index()

student_info['binary_label'] = student_info['final_result'].apply(lambda x: 1 if x in ['Fail','Withdraw'] else 0)
labels_df = student_info[['id_student','binary_label']]

data = sequences_df.merge(labels_df, on='id_student', how='inner')

data = data[data['event'].map(len) > 1].reset_index(drop=True)

success = data[data['binary_label']==0].sample(n=3000, random_state=42)
failure = data[data['binary_label']==1].sample(n=3000, random_state=42)

balanced_data = pd.concat([success, failure]).reset_index(drop=True)
balanced_data = balanced_data.sample(frac=1, random_state=42).reset_index(drop=True)

def sequence_to_dat(row):
    items = [str(row['binary_label'])]
    for e in row['event']:
        items.append(e)
        items.append('-1')
    items.append('-2')
    return ' '.join(items)

balanced_data['dat_sequence'] = balanced_data.apply(sequence_to_dat, axis=1)

dat_path = 'data/original/student_sequences_plus.dat'
with open(dat_path, 'w') as f:
    for seq in balanced_data['dat_sequence']:
        f.write(seq + '\n')

print(f".dat file saved at: {dat_path}")
print("Sample sequence:")
print(balanced_data['dat_sequence'].iloc[0])