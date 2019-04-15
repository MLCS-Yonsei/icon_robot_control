

class KnownFaces:
    def __init__(self, data_remove_time):

        self.encodings = []
        self.groups = []
        self.names = []
        self.times = []
        self.ids = []
        self.ages = []
        self.genders = []
        self.emotions = []
        self.emotion_probs = []
        self.detect_count = []

        self.index_in_data = []
        self.data_remove_time = data_remove_time



    def add_name(self, name, emotion_prob):
        self.genders.append(name.gender)
        self.ages.append(name.age)
        self.emotions.append(name.emotion)
        self.emotion_probs.append(emotion_prob)

    def add_data(self, time, name, track_id):
        self.times.append(time)
        self.names.append(name)
        self.ids.append(track_id)
        self.detect_count.append(1)
        self.index_in_data.append(len(self.names)-1)



    def update_name(self, index, name, emotion_prob):
        self.genders[index] = name.gender
        self.ages[index] = name.age
        self.emotions[index] = name.emotion
        self.emotion_probs[index] = emotion_prob

    def update_data(self, index, time, name):
        self.times[index] = time
        self.names[index] = name
        self.detect_count[index] += 1


    def read(self):
        pass

    def remove_olds(self, current_time):
        new_times = self.times
        for i, time in enumerate(self.times):
            if current_time - time > self.data_remove_time:
                del self.encodings[i]
                del self.names[i]
                del new_times[i]

        self.times = new_times

    def delete(self):
        pass


class Name:
    def __init__(self, track_id, gender=None, age=None, emotion=None):
        self.track_id = track_id
        self.gender = gender
        self.age = age
        self.emotion = emotion

    def __str__(self):
        return "ID: {}".format(self.track_id)

    def to_text(self):
        return "ID:{}, G:{}, A:{}, E: {}".format(self.track_id, self.gender, self.age, self.emotion)

#
# class Group:
#     def __init__(self, title, member):
#         self.title = title
#         self.member = member








