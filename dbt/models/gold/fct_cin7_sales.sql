with sales as (
    select * from {{ ref('stg_cin7__sales') }}
),

addresses as (
    select
        customer_id,
        city,
        country,
        postcode,
        postcode_area
    from {{ ref('stg_cin7__customer_addresses') }}
    where address_type = 'Shipping'
      and is_default = true
    qualify row_number() over (partition by customer_id order by address_id) = 1
),

with_order_num as (
    select
        s.*,
        row_number() over (
            partition by s.customer_id
            order by s.ordered_at
        ) as customer_order_number,
        a.city              as shipping_city,
        a.country           as shipping_country,
        a.postcode          as shipping_postcode,
        a.postcode_area,
        case a.postcode_area
            when 'E'  then 'London' when 'EC' then 'London' when 'N'  then 'London'
            when 'NW' then 'London' when 'SE' then 'London' when 'SW' then 'London'
            when 'W'  then 'London' when 'WC' then 'London' when 'BR' then 'London'
            when 'CR' then 'London' when 'DA' then 'London' when 'EN' then 'London'
            when 'HA' then 'London' when 'IG' then 'London' when 'KT' then 'London'
            when 'RM' then 'London' when 'SM' then 'London' when 'TW' then 'London'
            when 'UB' then 'London' when 'WD' then 'London'
            when 'BN' then 'South East' when 'CT' then 'South East'
            when 'GU' then 'South East' when 'ME' then 'South East'
            when 'OX' then 'South East' when 'PO' then 'South East'
            when 'RG' then 'South East' when 'RH' then 'South East'
            when 'SL' then 'South East' when 'SO' then 'South East'
            when 'TN' then 'South East'
            when 'BA' then 'South West' when 'BS' then 'South West'
            when 'DT' then 'South West' when 'EX' then 'South West'
            when 'GL' then 'South West' when 'PL' then 'South West'
            when 'SN' then 'South West' when 'TA' then 'South West'
            when 'TQ' then 'South West' when 'TR' then 'South West'
            when 'AL' then 'East of England' when 'CB' then 'East of England'
            when 'CM' then 'East of England' when 'CO' then 'East of England'
            when 'IP' then 'East of England' when 'LU' then 'East of England'
            when 'NR' then 'East of England' when 'PE' then 'East of England'
            when 'SG' then 'East of England' when 'SS' then 'East of England'
            when 'CV' then 'East Midlands' when 'DE' then 'East Midlands'
            when 'LE' then 'East Midlands' when 'LN' then 'East Midlands'
            when 'NG' then 'East Midlands' when 'NN' then 'East Midlands'
            when 'B'  then 'West Midlands' when 'DY' then 'West Midlands'
            when 'ST' then 'West Midlands' when 'WR' then 'West Midlands'
            when 'WS' then 'West Midlands' when 'WV' then 'West Midlands'
            when 'BD' then 'Yorkshire' when 'DN' then 'Yorkshire'
            when 'HD' then 'Yorkshire' when 'HG' then 'Yorkshire'
            when 'HU' then 'Yorkshire' when 'HX' then 'Yorkshire'
            when 'LS' then 'Yorkshire' when 'S'  then 'Yorkshire'
            when 'WF' then 'Yorkshire' when 'YO' then 'Yorkshire'
            when 'BB' then 'North West' when 'BL' then 'North West'
            when 'CA' then 'North West' when 'CH' then 'North West'
            when 'CW' then 'North West' when 'FY' then 'North West'
            when 'L'  then 'North West' when 'LA' then 'North West'
            when 'M'  then 'North West' when 'OL' then 'North West'
            when 'PR' then 'North West' when 'SK' then 'North West'
            when 'WA' then 'North West' when 'WN' then 'North West'
            when 'DH' then 'North East' when 'DL' then 'North East'
            when 'NE' then 'North East' when 'SR' then 'North East'
            when 'TS' then 'North East'
            when 'AB' then 'Scotland' when 'DD' then 'Scotland'
            when 'DG' then 'Scotland' when 'EH' then 'Scotland'
            when 'FK' then 'Scotland' when 'G'  then 'Scotland'
            when 'HS' then 'Scotland' when 'IV' then 'Scotland'
            when 'KA' then 'Scotland' when 'KW' then 'Scotland'
            when 'KY' then 'Scotland' when 'ML' then 'Scotland'
            when 'PA' then 'Scotland' when 'PH' then 'Scotland'
            when 'TD' then 'Scotland' when 'ZE' then 'Scotland'
            when 'CF' then 'Wales' when 'LD' then 'Wales'
            when 'LL' then 'Wales' when 'NP' then 'Wales'
            when 'SA' then 'Wales' when 'SY' then 'Wales'
            when 'BT' then 'Northern Ireland'
            else 'International'
        end                 as uk_region
    from sales s
    left join addresses a on s.customer_id = a.customer_id
)

select
    *,
    customer_order_number = 1 as is_first_order
from with_order_num
