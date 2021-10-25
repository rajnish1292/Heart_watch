from rest_framework import viewsets, status
from .serializers import heart_rate_Serializer, heart_rate_get_Serializer
from .models import heart_rate_data, PPG_data
from rest_framework.response import Response
from .PPG.ppg_hr import *
import datetime
import time
import json
from .PPG.custom_modules import decimal_to_binary


# Create your views here.


class heart_rate_ViewSet(viewsets.ModelViewSet):
    queryset = PPG_data.objects.all()
    serializer_class = heart_rate_Serializer

    def post(self, request, format=None):
        serializer = heart_rate_Serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class proccess_heart_rate_data(viewsets.ModelViewSet):
    queryset = PPG_data.objects.all()

    def get_serializer_class(self):
        return heart_rate_get_Serializer

    def list(self, request, *args, **kwargs):
        heart_rate_data_list = []
        ppg_instance = PPG_data.objects.all().order_by('-id')[:30]

        serializer = heart_rate_get_Serializer(ppg_instance, many=True)
        heart_rate_insta = serializer.data
        # print(heart_rate_insta)

        for i in heart_rate_insta:
            gg = i['heart_rate_voltage']
            heart_rate_data_list.append(gg)

        # print(heart_rate_data_list)
        # call ailments_stats method
        result = self.ailments_stats(heart_rate_data_list)

        # print(result)

        return Response(result)

    def ailments_stats(self, ppg_list):

        strike = 0
        strike_tachy = 0
        strike_afib = 0
        count = 20
        count_afib = 10
        brady_in = False
        tachy_in = False
        afib_in = False
        data_valid = True
        ppg_bytes = []
        time_val = []

        # reading of the input file starts here
        for ind in range(len(ppg_list)):
            a = ppg_list[ind].replace('\"', '')
            json_acceptable_string = a.replace('\\', '').replace("'", '"')
            ppg_data = json.loads(json_acceptable_string)
            ppg_sec = ppg_data['heart_rate_voltage']['data']
            time_val.append(ppg_data['heart_rate_voltage']['app_date'].split()[1])
            for j in range(2, len(ppg_sec), 3):
                ppg_bytes.append(decimal_to_binary(ppg_sec[j + 1]) + decimal_to_binary(ppg_sec[j]))
        ppg_sig = []
        for i in range(len(ppg_bytes)):
            ppg_sig.append(as_signed_big(ppg_bytes[i]))
        ppg_sig = np.asarray(ppg_sig)

        time_step_v = []
        for i in range(len(time_val)):

            x = time.strptime(time_val[i].split(',')[0], '%H:%M:%S')
            time_step_v.append(datetime.timedelta(hours=x.tm_hour, minutes=x.tm_min, seconds=x.tm_sec).total_seconds())

            if len(time_step_v) > 2:
                if time_step_v[-2] - time_step_v[-1] > 120:
                    data_valid = False
        if data_valid:
            final_pr, ppg_21, ppg_sig, ppg_bpf, t_diff_afib, hr_extracted = ppg_plot_hr(ppg_sig, time_val)

            for i in range(len(hr_extracted)):
                if 60 > hr_extracted[i] >= 40:
                    strike += 1
                else:
                    strike = 0

                if strike == count:
                    # print('Patient has Sinus Bradycardia')
                    brady_in = True

                    # One API call for Bradycardia

                if 100 < hr_extracted[i] <= 130:
                    strike_tachy += 1
                else:
                    strike_tachy = 0

                if strike_tachy == count:
                    # print('Patient has Sinus Tachycardia')
                    tachy_in = True

                    # One API call for Tachycardia

            for i in range(len(t_diff_afib) - 1):
                if t_diff_afib[i + 1] - t_diff_afib[i] > 10:
                    strike_afib += 1
                else:
                    strike_afib = 0
                if strike_afib == count_afib:
                    # print('Patient has Atrial Fibrillation')
                    afib_in = True

            # One API call for Atrial Fibrillation
            # return ppg_sig, hr_extracted, final_pr, afib_in, tachy_in, brady_in, data_valid
            return afib_in, tachy_in, brady_in

        else:
            statement = 'Data missing for over 2 minutes , PPG analysis not done'
            return 0
