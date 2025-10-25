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
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: root
--

INSERT INTO public.users VALUES ('e1d31159-900b-4085-a886-182269116087', 'Jarkko', 'jarkko.sissala@gmail.com', '$2b$12$EQb6vyh096osuYvsCH.YqOfIbSF6kNPO/63f8kyv5Vpi6LWfSNksa', '2025-09-19 08:47:49.83382+00', '2025-09-19 08:47:49.833827+00', false, '2025-09-19 08:48:13.983687+00', 1);
INSERT INTO public.users VALUES ('9b7931e2-0df2-40df-a8e6-5bcd4f138772', 'testuser', 'test@example.com', '$2b$12$KS5QgtS4T9eVnPCvC7C35e0LawXAiVZovCAQgHOq93.VFz.3aHrg.', '2025-09-17 17:44:39.260716+00', '2025-09-21 08:50:37.632166+00', false, NULL, 4);
INSERT INTO public.users VALUES ('b00abbd0-bad9-414b-ab87-c46b422f3780', 'admin', 'admin@example.com', '$2b$12$tvVJ8ZVy6otFBOJnP9zrUucw7FELTBNVDUXSOV3.NFdj1fJQGa8W6', '2025-09-17 17:31:44.336779+00', '2025-09-19 14:20:46.978344+00', true, '2025-09-19 18:16:40.288439+00', 1);


--
-- PostgreSQL database dump complete
--

