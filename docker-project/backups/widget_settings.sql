--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13
-- Dumped by pg_dump version 15.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: user_widget_settings; Type: TABLE DATA; Schema: public; Owner: root
--

INSERT INTO public.user_widget_settings VALUES (440, 'e1d31159-900b-4085-a886-182269116087', 'cpu-usage', true, '2025-09-19 13:06:48.563366', '2025-09-19 13:06:48.563366');
INSERT INTO public.user_widget_settings VALUES (441, 'e1d31159-900b-4085-a886-182269116087', 'system-health', false, '2025-09-19 13:06:48.563366', '2025-09-19 13:06:48.563366');
INSERT INTO public.user_widget_settings VALUES (442, 'e1d31159-900b-4085-a886-182269116087', 'memory-usage', true, '2025-09-19 13:06:48.563366', '2025-09-19 13:06:48.563366');
INSERT INTO public.user_widget_settings VALUES (443, 'e1d31159-900b-4085-a886-182269116087', 'disk-usage', true, '2025-09-19 13:06:48.563366', '2025-09-19 13:06:48.563366');
INSERT INTO public.user_widget_settings VALUES (444, 'e1d31159-900b-4085-a886-182269116087', 'network-usage', false, '2025-09-19 13:06:48.563366', '2025-09-19 13:06:48.563366');
INSERT INTO public.user_widget_settings VALUES (445, 'e1d31159-900b-4085-a886-182269116087', 'database-size', true, '2025-09-19 13:06:48.563366', '2025-09-19 13:06:48.563366');
INSERT INTO public.user_widget_settings VALUES (446, 'e1d31159-900b-4085-a886-182269116087', 'container-status', true, '2025-09-19 13:06:48.563366', '2025-09-19 13:06:48.563366');
INSERT INTO public.user_widget_settings VALUES (447, 'e1d31159-900b-4085-a886-182269116087', 'user-count', false, '2025-09-19 13:06:48.563366', '2025-09-19 13:06:48.563366');
INSERT INTO public.user_widget_settings VALUES (448, 'e1d31159-900b-4085-a886-182269116087', 'uptime', false, '2025-09-19 13:06:48.563366', '2025-09-19 13:06:48.563366');
INSERT INTO public.user_widget_settings VALUES (449, 'e1d31159-900b-4085-a886-182269116087', 'amd-stock', true, '2025-09-19 13:06:48.563366', '2025-09-19 13:06:48.563366');
INSERT INTO public.user_widget_settings VALUES (450, 'e1d31159-900b-4085-a886-182269116087', 'lahti-weather', true, '2025-09-19 13:06:48.563366', '2025-09-19 13:06:48.563366');
INSERT INTO public.user_widget_settings VALUES (451, 'e1d31159-900b-4085-a886-182269116087', 'mikkeli-weather', true, '2025-09-19 13:06:48.563366', '2025-09-19 13:06:48.563366');
INSERT INTO public.user_widget_settings VALUES (452, 'e1d31159-900b-4085-a886-182269116087', 'rauma-weather', true, '2025-09-19 13:06:48.563366', '2025-09-19 13:06:48.563366');
INSERT INTO public.user_widget_settings VALUES (453, 'e1d31159-900b-4085-a886-182269116087', 'il-belt-valletta-weather', true, '2025-09-19 13:06:48.563366', '2025-09-19 13:06:48.563366');
INSERT INTO public.user_widget_settings VALUES (924, 'b00abbd0-bad9-414b-ab87-c46b422f3780', 'cpu-usage', true, '2025-10-05 19:44:29.778083', '2025-10-05 19:44:29.778083');
INSERT INTO public.user_widget_settings VALUES (925, 'b00abbd0-bad9-414b-ab87-c46b422f3780', 'system-health', false, '2025-10-05 19:44:29.778083', '2025-10-05 19:44:29.778083');
INSERT INTO public.user_widget_settings VALUES (926, 'b00abbd0-bad9-414b-ab87-c46b422f3780', 'memory-usage', true, '2025-10-05 19:44:29.778083', '2025-10-05 19:44:29.778083');
INSERT INTO public.user_widget_settings VALUES (927, 'b00abbd0-bad9-414b-ab87-c46b422f3780', 'disk-usage', false, '2025-10-05 19:44:29.778083', '2025-10-05 19:44:29.778083');
INSERT INTO public.user_widget_settings VALUES (928, 'b00abbd0-bad9-414b-ab87-c46b422f3780', 'network-usage', false, '2025-10-05 19:44:29.778083', '2025-10-05 19:44:29.778083');
INSERT INTO public.user_widget_settings VALUES (929, 'b00abbd0-bad9-414b-ab87-c46b422f3780', 'database-size', true, '2025-10-05 19:44:29.778083', '2025-10-05 19:44:29.778083');
INSERT INTO public.user_widget_settings VALUES (930, 'b00abbd0-bad9-414b-ab87-c46b422f3780', 'container-status', true, '2025-10-05 19:44:29.778083', '2025-10-05 19:44:29.778083');
INSERT INTO public.user_widget_settings VALUES (931, 'b00abbd0-bad9-414b-ab87-c46b422f3780', 'user-count', false, '2025-10-05 19:44:29.778083', '2025-10-05 19:44:29.778083');
INSERT INTO public.user_widget_settings VALUES (932, 'b00abbd0-bad9-414b-ab87-c46b422f3780', 'uptime', false, '2025-10-05 19:44:29.778083', '2025-10-05 19:44:29.778083');
INSERT INTO public.user_widget_settings VALUES (933, 'b00abbd0-bad9-414b-ab87-c46b422f3780', '^ixic-stock', true, '2025-10-05 19:44:29.778083', '2025-10-05 19:44:29.778083');
INSERT INTO public.user_widget_settings VALUES (934, 'b00abbd0-bad9-414b-ab87-c46b422f3780', 'amd-stock', true, '2025-10-05 19:44:29.778083', '2025-10-05 19:44:29.778083');
INSERT INTO public.user_widget_settings VALUES (935, 'b00abbd0-bad9-414b-ab87-c46b422f3780', 'grindelwald-weather', false, '2025-10-05 19:44:29.778083', '2025-10-05 19:44:29.778083');
INSERT INTO public.user_widget_settings VALUES (936, 'b00abbd0-bad9-414b-ab87-c46b422f3780', 'il-belt-valletta-weather', true, '2025-10-05 19:44:29.778083', '2025-10-05 19:44:29.778083');
INSERT INTO public.user_widget_settings VALUES (937, 'b00abbd0-bad9-414b-ab87-c46b422f3780', 'lahti-weather', true, '2025-10-05 19:44:29.778083', '2025-10-05 19:44:29.778083');
INSERT INTO public.user_widget_settings VALUES (938, 'b00abbd0-bad9-414b-ab87-c46b422f3780', 'mikkeli-weather', true, '2025-10-05 19:44:29.778083', '2025-10-05 19:44:29.778083');
INSERT INTO public.user_widget_settings VALUES (939, 'b00abbd0-bad9-414b-ab87-c46b422f3780', 'rauma-weather', true, '2025-10-05 19:44:29.778083', '2025-10-05 19:44:29.778083');


--
-- Name: user_widget_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: root
--

SELECT pg_catalog.setval('public.user_widget_settings_id_seq', 939, true);


--
-- PostgreSQL database dump complete
--

