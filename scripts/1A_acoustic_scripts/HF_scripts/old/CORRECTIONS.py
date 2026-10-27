'''
************************************************************
CORRECTIONS TO HIGH-FREQUENCY DATA (PAMGUARD EXPORT) FOR MISSION UVI2_AROUND_STX_20250306
WAITING ON CONFIRMATION FROM HELOISE FOR 11 CLICK EVENTS
************************************************************
'''


#✦ POSSIBLE GERVAIS' BEAKED WHALE DETECTIONS (me) :
#   Id   UID     UTC                         PCTime                      EventEnd                    eventType   nClicks     colour      comment         
#⟣ 19   19      2025-03-07 00:47:44.347     2026-06-24 06:48:20.372     2025-03-07 00:47:45.451     me          3           10          ASK HELOISE     
#༝  20   20      2025-03-07 01:02:57.660     2026-06-24 02:27:21.647     2025-03-07 01:02:58.660	 me	         3	         10	         ASK HELOISE     
#⟣ 478  3908    2025-03-15 08:33:31.872	    2026-06-23 22:22:21.695	    2025-03-15 08:33:33.041	    me	        3	        10	        ASK HELOISE     
#༝  760  6042    2025-03-20 14:47:48.594	 2026-06-24 03:29:25.276	 2025-03-20 14:48:13.020	 me          17	         10	         ASK HELOISE     
#⟣ 802  6085    2025-03-21 19:43:07.421	    2026-06-24 04:03:55.315	    2025-03-21 19:43:27.213	    me	        8	        10	        ASK HELOISE     
#༝  940  7902    2025-03-23 05:27:47.323	 2026-06-24 05:53:32.932	 2025-03-23 05:27:49.649	 me	         6	         10          ASK HELOISE     


#❥ POSSIBLE GOOSE-BEAKED WHALE DETECTIONS (zc) :
#   Id   UID     UTC                         PCTime                      EventEnd                    eventType   nClicks     colour      comment         
#◜  432  3429	 2025-03-14 13:22:47.566	 2026-06-24 06:57:00.199	 2025-03-14 13:22:58.269	 zc	         23	         10	         ASK HELOISE     
#⊹  783  6065	 2025-03-21 08:08:25.142	 2026-06-24 03:52:52.021	 2025-03-21 08:08:25.883	 zc	         2	         10	         ASK HELOISE (for time check 2025-03-21 08:07:44 UTC)    


#❋ UO OR JUST HUMPBACKS? :
#   Id   UID     UTC                         PCTime                      EventEnd                    eventType   nClicks     colour      comment    
#✧  406  3403	 2025-03-14 03:22:46.851	 2026-06-23 21:56:32.202	 2025-03-14 03:23:16.102	 uo	         31	         10	         uo or just humpbacks??


#˓ WTF **DOES NOOOOTTTTT NEED CORRECTION BECAUSE WILL BE SURFACING (SURF) MIN REGARDLESS** :
#˓  Id   UID      UTC                         PCTime                      EventEnd                    eventType   nClicks     colour      comment   
#˓  399  3396	  2025-03-14 02:37:45.566	  2026-06-23 21:55:05.350	  2025-03-14 02:38:30.849	  surf	      3132	      10	      WTF       




################################################################################################################################################
################################################################################################################################################



#✦ #############################################################################################################################################
#✦ Dictionary of manual fixes: rawexport_pamguard_sqlite_click_detector_offlineevents_UVI2_Around_STX_20250306.csv

#༝  IF need to change me -> uo
#◦ (Id, UID, "UTC", "PCTime", "EventEnd", "eventType", nClicks, colour): {"eventType": "uo", "colour": 4, "comment": "heloise - not gervais"}
me_uo_fix = {
    (19, 19, "2025-03-07 00:47:44.347", "2026-06-24 06:48:20.372", "2025-03-07 00:47:45.451", "me", 3, 10): {"eventType": "uo", "colour": 4, "comment": "heloise - not gervais"},
    #etc...
}

#༝  IF me is correct
#◦ (Id, UID, "UTC", "PCTime", "EventEnd", "eventType", nClicks, colour): {"colour": 2, "comment": "confirmed by heloise"}
me_correct = {
    (19, 19, "2025-03-07 00:47:44.347", "2026-06-24 06:48:20.372", "2025-03-07 00:47:45.451", "me", 3, 10): {"colour": 2, "comment": "confirmed by heloise"},
    #etc...
}
#✦ #############################################################################################################################################


#❥ #############################################################################################################################################
#❥ Dictionary of manual fixes: rawexport_pamguard_sqlite_click_detector_offlineevents_UVI2_Around_STX_20250306.csv

#❋  IF need to change zc -> uo
#༚ (Id, UID, "UTC", "PCTime", "EventEnd", "eventType", nClicks, colour): {"eventType": "uo", "colour": 4, "comment": "heloise - not goose"}
zc_uo_fix1 = {
    (19, 19, "2025-03-07 00:47:44.347", "2026-06-24 06:48:20.372", "2025-03-07 00:47:45.451", "me", 3, 10): {"eventType": "uo", "colour": 4, "comment": "heloise - not goose"}
}

#❋  IF zc is correct
#༚ (Id, UID, "UTC", "PCTime", "EventEnd", "eventType", nClicks, colour): {"colour": 2, "comment": "confirmed by heloise"}
zc_correct1 = {
    (19, 19, "2025-03-07 00:47:44.347", "2026-06-24 06:48:20.372", "2025-03-07 00:47:45.451", "me", 3, 10): {"colour": 2, "comment": "confirmed by heloise"}
}
#❥ #############################################################################################################################################











#ㅱ RE-RUN SCRIPTS FROM 4_tidy_pamguard_export_clicks.py AND ON!!! (rest of HF acoustic scripts -> interpolation HF scripts -> ??????)