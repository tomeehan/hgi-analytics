{{ config(materialized='table') }}

-- GA4 traffic-and-conversion fact, one row per session_date × store_id.
-- Sessions and GA-attributed revenue come from the source/medium report;
-- users from the website-overview report; transactions from the purchase
-- event count. Users and transactions are left-joined onto the sessions
-- grain so a day with sessions but no users / transactions row still
-- appears, with the joined-in counts coalesced to 0.

with sessions as (
    select * from {{ ref('stg_google_analytics__sessions') }}
),

users as (
    select * from {{ ref('stg_google_analytics__users') }}
),

transactions as (
    select * from {{ ref('stg_google_analytics__transactions') }}
)

select
    sessions.session_date,
    sessions.order_month,
    sessions.store_id,
    sessions.sessions,
    sessions.engaged_sessions,
    sessions.total_revenue,
    coalesce(users.users, 0) as users,
    coalesce(transactions.transactions, 0) as transactions
from sessions
left join users
    on sessions.session_date = users.session_date
    and sessions.store_id = users.store_id
left join transactions
    on sessions.session_date = transactions.session_date
    and sessions.store_id = transactions.store_id
