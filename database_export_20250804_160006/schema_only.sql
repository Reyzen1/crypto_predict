--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.price_data DROP CONSTRAINT IF EXISTS price_data_crypto_id_fkey;
ALTER TABLE IF EXISTS ONLY public.predictions DROP CONSTRAINT IF EXISTS predictions_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.predictions DROP CONSTRAINT IF EXISTS predictions_crypto_id_fkey;
DROP INDEX IF EXISTS public.ix_users_id;
DROP INDEX IF EXISTS public.ix_users_email;
DROP INDEX IF EXISTS public.ix_price_data_timestamp;
DROP INDEX IF EXISTS public.ix_price_data_id;
DROP INDEX IF EXISTS public.ix_price_data_crypto_id;
DROP INDEX IF EXISTS public.ix_predictions_user_id;
DROP INDEX IF EXISTS public.ix_predictions_target_datetime;
DROP INDEX IF EXISTS public.ix_predictions_model_name;
DROP INDEX IF EXISTS public.ix_predictions_id;
DROP INDEX IF EXISTS public.ix_predictions_crypto_id;
DROP INDEX IF EXISTS public.ix_predictions_created_at;
DROP INDEX IF EXISTS public.ix_cryptocurrencies_symbol;
DROP INDEX IF EXISTS public.ix_cryptocurrencies_id;
DROP INDEX IF EXISTS public.ix_cryptocurrencies_coingecko_id;
DROP INDEX IF EXISTS public.idx_price_crypto_timestamp;
DROP INDEX IF EXISTS public.idx_prediction_user_created;
DROP INDEX IF EXISTS public.idx_prediction_realized;
DROP INDEX IF EXISTS public.idx_prediction_model_performance;
DROP INDEX IF EXISTS public.idx_prediction_model_created;
DROP INDEX IF EXISTS public.idx_prediction_horizon;
DROP INDEX IF EXISTS public.idx_prediction_crypto_target;
DROP INDEX IF EXISTS public.idx_crypto_updated;
DROP INDEX IF EXISTS public.idx_crypto_symbol_active;
DROP INDEX IF EXISTS public.idx_crypto_rank;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.price_data DROP CONSTRAINT IF EXISTS price_data_pkey;
ALTER TABLE IF EXISTS ONLY public.predictions DROP CONSTRAINT IF EXISTS predictions_pkey;
ALTER TABLE IF EXISTS ONLY public.cryptocurrencies DROP CONSTRAINT IF EXISTS cryptocurrencies_pkey;
ALTER TABLE IF EXISTS public.users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.price_data ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.predictions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.cryptocurrencies ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.users_id_seq;
DROP TABLE IF EXISTS public.users;
DROP SEQUENCE IF EXISTS public.price_data_id_seq;
DROP TABLE IF EXISTS public.price_data;
DROP SEQUENCE IF EXISTS public.predictions_id_seq;
DROP TABLE IF EXISTS public.predictions;
DROP SEQUENCE IF EXISTS public.cryptocurrencies_id_seq;
DROP TABLE IF EXISTS public.cryptocurrencies;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: cryptocurrencies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cryptocurrencies (
    id integer NOT NULL,
    symbol character varying(10) NOT NULL,
    name character varying(100) NOT NULL,
    coingecko_id character varying(50),
    market_cap_rank integer,
    current_price numeric(20,8),
    market_cap numeric(30,2),
    total_volume numeric(30,2),
    circulating_supply numeric(30,2),
    total_supply numeric(30,2),
    max_supply numeric(30,2),
    description text,
    website_url character varying(255),
    blockchain_site character varying(255),
    is_active boolean NOT NULL,
    is_supported boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    last_data_update timestamp with time zone
);


--
-- Name: cryptocurrencies_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cryptocurrencies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cryptocurrencies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cryptocurrencies_id_seq OWNED BY public.cryptocurrencies.id;


--
-- Name: predictions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.predictions (
    id integer NOT NULL,
    crypto_id integer NOT NULL,
    user_id integer,
    model_name character varying(50) NOT NULL,
    model_version character varying(20) NOT NULL,
    predicted_price numeric(20,8) NOT NULL,
    confidence_score numeric(5,4) NOT NULL,
    prediction_horizon integer NOT NULL,
    target_datetime timestamp with time zone NOT NULL,
    features_used json,
    model_parameters json,
    input_price numeric(20,8) NOT NULL,
    input_features json,
    actual_price numeric(20,8),
    accuracy_percentage numeric(5,2),
    absolute_error numeric(20,8),
    squared_error numeric(30,8),
    is_realized boolean NOT NULL,
    is_accurate boolean,
    accuracy_threshold numeric(5,2),
    training_data_end timestamp with time zone,
    market_conditions character varying(20),
    volatility_level character varying(10),
    model_training_time numeric(10,2),
    prediction_time numeric(10,6),
    notes text,
    debug_info json,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now(),
    evaluated_at timestamp with time zone
);


--
-- Name: predictions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.predictions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: predictions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.predictions_id_seq OWNED BY public.predictions.id;


--
-- Name: price_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.price_data (
    id integer NOT NULL,
    crypto_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    open_price numeric(20,8) NOT NULL,
    high_price numeric(20,8) NOT NULL,
    low_price numeric(20,8) NOT NULL,
    close_price numeric(20,8) NOT NULL,
    volume numeric(30,8),
    market_cap numeric(30,2),
    created_at timestamp with time zone
);


--
-- Name: price_data_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.price_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: price_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.price_data_id_seq OWNED BY public.price_data.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    first_name character varying(50),
    last_name character varying(50),
    is_active boolean,
    is_verified boolean,
    is_superuser boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    last_login timestamp with time zone,
    preferences text
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: cryptocurrencies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cryptocurrencies ALTER COLUMN id SET DEFAULT nextval('public.cryptocurrencies_id_seq'::regclass);


--
-- Name: predictions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions ALTER COLUMN id SET DEFAULT nextval('public.predictions_id_seq'::regclass);


--
-- Name: price_data id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.price_data ALTER COLUMN id SET DEFAULT nextval('public.price_data_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: cryptocurrencies cryptocurrencies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cryptocurrencies
    ADD CONSTRAINT cryptocurrencies_pkey PRIMARY KEY (id);


--
-- Name: predictions predictions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_pkey PRIMARY KEY (id);


--
-- Name: price_data price_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.price_data
    ADD CONSTRAINT price_data_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_crypto_rank; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_crypto_rank ON public.cryptocurrencies USING btree (market_cap_rank);


--
-- Name: idx_crypto_symbol_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_crypto_symbol_active ON public.cryptocurrencies USING btree (symbol, is_active);


--
-- Name: idx_crypto_updated; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_crypto_updated ON public.cryptocurrencies USING btree (updated_at);


--
-- Name: idx_prediction_crypto_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prediction_crypto_target ON public.predictions USING btree (crypto_id, target_datetime);


--
-- Name: idx_prediction_horizon; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prediction_horizon ON public.predictions USING btree (prediction_horizon, created_at);


--
-- Name: idx_prediction_model_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prediction_model_created ON public.predictions USING btree (model_name, created_at);


--
-- Name: idx_prediction_model_performance; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prediction_model_performance ON public.predictions USING btree (model_name, model_version, confidence_score);


--
-- Name: idx_prediction_realized; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prediction_realized ON public.predictions USING btree (is_realized, accuracy_percentage);


--
-- Name: idx_prediction_user_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prediction_user_created ON public.predictions USING btree (user_id, created_at);


--
-- Name: idx_price_crypto_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_price_crypto_timestamp ON public.price_data USING btree (crypto_id, "timestamp");


--
-- Name: ix_cryptocurrencies_coingecko_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_cryptocurrencies_coingecko_id ON public.cryptocurrencies USING btree (coingecko_id);


--
-- Name: ix_cryptocurrencies_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cryptocurrencies_id ON public.cryptocurrencies USING btree (id);


--
-- Name: ix_cryptocurrencies_symbol; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_cryptocurrencies_symbol ON public.cryptocurrencies USING btree (symbol);


--
-- Name: ix_predictions_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_predictions_created_at ON public.predictions USING btree (created_at);


--
-- Name: ix_predictions_crypto_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_predictions_crypto_id ON public.predictions USING btree (crypto_id);


--
-- Name: ix_predictions_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_predictions_id ON public.predictions USING btree (id);


--
-- Name: ix_predictions_model_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_predictions_model_name ON public.predictions USING btree (model_name);


--
-- Name: ix_predictions_target_datetime; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_predictions_target_datetime ON public.predictions USING btree (target_datetime);


--
-- Name: ix_predictions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_predictions_user_id ON public.predictions USING btree (user_id);


--
-- Name: ix_price_data_crypto_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_price_data_crypto_id ON public.price_data USING btree (crypto_id);


--
-- Name: ix_price_data_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_price_data_id ON public.price_data USING btree (id);


--
-- Name: ix_price_data_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_price_data_timestamp ON public.price_data USING btree ("timestamp");


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: predictions predictions_crypto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_crypto_id_fkey FOREIGN KEY (crypto_id) REFERENCES public.cryptocurrencies(id);


--
-- Name: predictions predictions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: price_data price_data_crypto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.price_data
    ADD CONSTRAINT price_data_crypto_id_fkey FOREIGN KEY (crypto_id) REFERENCES public.cryptocurrencies(id);


--
-- PostgreSQL database dump complete
--

