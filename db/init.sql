CREATE TABLE public.cards (
    "ID" integer NOT NULL,
    name character varying,
    cost integer,
    image character varying
);

ALTER TABLE public.cards ALTER COLUMN "ID" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public."cards_ID_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

CREATE TABLE public.improvements (
    "ID" bigint NOT NULL,
    cost integer NOT NULL,
    add integer DEFAULT 1 NOT NULL,
    energy integer DEFAULT 1000 NOT NULL
);

ALTER TABLE public.improvements ALTER COLUMN "ID" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public."improvements_ID_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

CREATE TABLE public.improvements_energy (
    "ID" integer NOT NULL,
    energy integer NOT NULL,
    cost integer
);

ALTER TABLE public.improvements_energy ALTER COLUMN "ID" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public."improvements_energy_ID_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

CREATE TABLE public.inventory (
    "ID" integer NOT NULL,
    "ID_card" bigint NOT NULL,
    "ID_user" bigint NOT NULL
);

ALTER TABLE public.inventory ALTER COLUMN "ID" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public."inventory_ID_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

CREATE TABLE public.score (
    score integer DEFAULT 5000 NOT NULL,
    "ID" integer NOT NULL,
    "ID_user" bigint NOT NULL,
    "ID_improvements" integer DEFAULT 1 NOT NULL,
    bot integer DEFAULT 0 NOT NULL,
    energy_lvl integer DEFAULT 1 NOT NULL,
    energy integer DEFAULT 500 NOT NULL
);

ALTER TABLE public.score ALTER COLUMN "ID" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public."score_ID_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 100000000
    CACHE 1
);

COPY public.improvements ("ID", cost, add, energy) FROM stdin;
2	1000	2	1000
1	500	1	500
3	1500	3	1500
4	2500	4	2000
5	5000	5	2500
6	15000	6	3000
7	25000	7	3500
8	50000	8	4000
9	75000	9	4500
10	100000	10	5000
11	200000	11	5500
12	400000	12	6000
13	800000	13	6500
14	1600000	14	7000
15	3200000	15	7500
16	6400000	16	8000
17	12800000	17	8500
18	25600000	18	9000
19	51200000	19	9500
20	102400000	20	10000
\.

COPY public.improvements_energy ("ID", energy, cost) FROM stdin;
1	500	500
2	1000	1000
3	1500	1500
4	2000	2500
5	2500	5000
6	3000	15000
7	3500	25000
8	4000	50000
9	4500	75000
10	5000	100000
11	5500	200000
12	6000	400000
13	6500	800000
14	7000	1600000
15	7500	3200000
16	8000	6400000
17	8500	12800000
18	9000	25600000
19	9500	51200000
20	10000	102400000
\.

ALTER TABLE ONLY public.improvements
    ADD CONSTRAINT "Users_pkey" PRIMARY KEY ("ID");

ALTER TABLE ONLY public.cards
    ADD CONSTRAINT cards_pkey PRIMARY KEY ("ID");

ALTER TABLE ONLY public.improvements_energy
    ADD CONSTRAINT improvements_energy_pkey PRIMARY KEY ("ID");

ALTER TABLE ONLY public.score
    ADD CONSTRAINT score_pkey PRIMARY KEY ("ID");