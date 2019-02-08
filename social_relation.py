

class SocialRelationEstimator:
    def __init__(self):
        '''
        0 : 최초 상태
        1 : 스캔 중
        2 : 발화 중 

        1일 경우 기존에 tracking 하던게 있는지 우선으로 보고 갈 것.
        -> ID를 체크해서 계속 같은 대상들을 추적하고 있을 경우, 가장 누적된 것으로 발화 
        '''   
        self.status = 0

    def _get_diff(self, l):
        return max(l) - min(l)
    
    def _get_avg(self, l):
        return sum(l) / float(len(l))

    def utterance_for_family(ages, genders):
        # if max(ages) > 35
        #     # 부모자식
        # else:
        #     # 형제/조카
        print("utterance_for_family", ages, genders)

    def utterance_for_couple(self, ages, genders):
        print("utterance_for_couple", ages, genders)

    def utterance_for_friends(self, ages, genders):
        print("utterance_for_friends", ages, genders)

    def utterance_for_kids(self, ages, genders):
        print("utterance_for_kids", ages, genders)

    def utterance_for_single(self, age, gender):
        print("utterance_for_single", age, gender)

    def run(self, detect_cnts, ages, genders):
        print(detect_cnts, ages, genders)
        if min(detect_cnts) > 10:
            if len(ages) == 1:
                self.utterance_for_single(ages[0], genders[0])
            elif len(ages) == 2:
                if genders[0] == genders[1]:
                    if self._get_diff(ages) <= 8:
                        if self._get_avg(ages) < 15:
                            # 아이들
                            self.utterance_for_kids(ages, genders)
                        else:
                            # 친구 혹은 형제자매
                            self.utterance_for_friends(ages, genders) 
                    else:
                        # 가족
                        self.utterance_for_family(ages, genders)

                else:
                    if self._get_diff(ages) <= 12:
                        if self._get_avg(ages) < 15:
                            # 아이들 
                            self.utterance_for_kids(ages, genders)
                        else:
                            # 커플
                            self.utterance_for_couple(ages, genders)
                    else:
                        # 가족 
                        self.utterance_for_family(ages, genders)
