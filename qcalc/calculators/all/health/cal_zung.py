# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

def zung__info():
    options1 = {
        'type': 'radio',
        # 'initial': 1,
        'choices': [
            {'name': 'None or a little of the time', 'value': 1},
            {'name': 'Some of the time', 'value': 2},
            {'name': 'Good part of the time', 'value': 3},
            {'name': 'Most or all of the time', 'value': 4}
        ],
    }

    options2 = {
        'type': 'radio',
        # 'initial': 4,
        'choices': [
            {'name': 'None or a little of the time', 'value': 4},
            {'name': 'Some of the time', 'value': 3},
            {'name': 'Good part of the time', 'value': 2},
            {'name': 'Most or all of the time', 'value': 1}
        ],
    }

    return {
        'title': 'Zung Self-Rating Depression Calculator',
        'schema': {
            'q01': {**options1, **{'label': 'I feel more nervous and anxious than usual'}},
            'q02': {**options1, **{'label': 'I feel afraid for no reason at all'}},
            'q03': {**options1, **{'label': 'I get upset easily or feel panicky'}},
            'q04': {**options1, **{'label': 'I feel like I’m falling apart and going to pieces'}},
            'q05': {**options2, **{'label': 'I feel that everything is all right and nothing bad will happen'}},
            'q06': {**options1, **{'label': 'My arms and legs shake and tremble'}},
            'q07': {**options1, **{'label': 'I am bothered by headaches, neck and back pains'}},
            'q08': {**options1, **{'label': 'I feel weak and get tired easily'}},
            'q09': {**options2, **{'label': 'I feel calm and and can sit still easily'}},
            'q10': {**options1, **{'label': 'I can feel my heart beating fast'}},
            'q11': {**options1, **{'label': 'I am bothered by dizzy spells'}},
            'q12': {**options1, **{'label': 'I have fainting spells or feel faint'}},
            'q13': {**options2, **{'label': 'I can breath in and out easily'}},
            'q14': {**options1, **{'label': 'I get feelings of numbness and tingling in my fingers and toes'}},
            'q15': {**options1, **{'label': 'I am bothered by stomachaches or indigestion'}},
            'q16': {**options1, **{'label': 'I have to empty my bladder often'}},
            'q17': {**options2, **{'label': 'My hands are usually dry and warm'}},
            'q18': {**options1, **{'label': 'My face gets hot and blushes'}},
            'q19': {**options2, **{'label': 'I fall asleep easily and get a good night’s rest'}},
            'q20': {**options1, **{'label': 'I have nightmares'}},
        },
        'col': ['q01-q10', 'q11-q20'],
        # 'template': 'v4.22',
    }


def zung(
    q01='1', q02='1', q03='1', q04='1', q05='4',
    q06='1', q07='1', q08='1', q09='4', q10='1',
    q11='1', q12='1', q13='4', q14='1', q15='1',
    q16='1', q17='4', q18='1', q19='4', q20='1'
):
    raw_score = int(q01) + int(q02) + int(q03) + int(q04) + int(q05) + \
                int(q06) + int(q07) + int(q08) + int(q09) + int(q10) + \
                int(q11) + int(q12) + int(q13) + int(q14) + int(q15) + \
                int(q16) + int(q17) + int(q18) + int(q19) + int(q20)
    ai = int(round(25 + (raw_score - 20) * 1.25, 0))  # anxiety_index
    desc = ''
    if ai < 45:
        desc = 'Within normal range'
    elif 45 <= ai <= 59:
        desc = 'Minimal to moderate anxiety'
    elif 60 <= ai <= 74:
        desc = 'Marked to severe anxiety'
    elif ai > 75:
        desc = 'Most extreme anxiety'

    return {
        'Anxiety Index': ai,
        'Anxiety Level': desc
    }
