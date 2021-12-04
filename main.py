import scrapy
from keywords import *
from scrapy.crawler import CrawlerProcess


class MySpider(scrapy.Spider):
    name = 'nist'
    base_url = 'https://nvd.nist.gov'
    allowed_domains = ['nvd.nist.gov']
    start_urls = ['https://nvd.nist.gov']

    def parse(self, response):
        keywords = getKeywords()
        for keyword in keywords:
            url = self.base_url + "/vuln/search/results?form_type=Basic&query=" + keyword + "&results_type=overview&search_type=all&startIndex=00"
            yield scrapy.Request(url, callback=self.parse_vuln_list)

    # parse the page containing the list of vulnerabilities
    def parse_vuln_list(self, response):
        cves = response.xpath("//th[@nowrap]/strong/a/@href").extract()
        for cve in cves: # parse the vulnerability
            url = self.base_url + cve
            yield scrapy.Request(url, callback=self.parse_page)

        # iterate over the different view pages
        total_vuln_str = response.xpath("//strong[@data-testid='vuln-matching-records-count']/text()").extract()[0] # extract the total number of vulnerabilities
        total_vuln = [str(s) for s in total_vuln_str if s.isdigit()] # isolate the digits
        total_vuln = int(''.join(total_vuln), base=10) #combine and convert into an integer
        count = 20
        while count < total_vuln: # iterate over the views
            url = str(response.request.url)[:-2] + str(count)
            count += 20
            yield scrapy.Request(url, callback=self.parse_vuln_list)

    # extract the needed data from the webpage
    def parse_page(self, response):
        id = response.xpath("//title/text()").extract_first()
        description = response.xpath("//p[@data-testid='vuln-description']/text()").get()
        references = response.xpath("//div[@id='vulnHyperlinksPanel']/table[@class='table table-striped table-condensed table-bordered detail-table']/tbody/tr/td/a/@href").extract();
        try:
            impact = response.xpath("//span[@class='severityDetail']/a/text()").extract()[0][0:3]
        except:
            impact = None
        #return the result
        return {'id': id, "impact": impact, "description": description, " references": references}


if __name__ == '__main__':
    # crawler settings
    process = CrawlerProcess(settings={
        "FEED_FORMAT": 'json',
        "FEED_URI": 'cve.json',
    })

    process.crawl(MySpider)
    process.start()