xbrl-parse
==========

Get historical fundamental data time series in Pandas Dataframes from SEC Edgar for any company. I couldn't find this anywhere in an easy to use way. Other options were very complicated and didn't work well across companies.

Requirements:<br>
beautifulsoup4<br>
pandas<br>

Usage:

Ask for historical data for a particular ticker and financial statement item, and it will return a Pandas DataFrame with all the series it was able to pull for that item. 'root' will always be the entity as a whole, but you might get back multiple series if the company has divisions geographically, or different business segments.

example:
```python
from xbrl_parse import Company

data = Company('MSFT')
print data.get_series_from_id('Assets')['root']

2009-06-30     77888000000
2009-09-30     81612000000
2009-12-31     82096000000
2010-03-31     84910000000
2010-06-30     86113000000
2010-09-30     91540000000
2010-12-31     92306000000
2011-03-31     99727000000
2011-06-30    108704000000
2011-09-30    107415000000
2011-12-31    112243000000
2012-03-31    118010000000
2012-06-30    121271000000
2012-09-30    121876000000
2012-12-31    128683000000
2013-03-31    134105000000
2013-06-30    142431000000
2013-09-30    142348000000
```
