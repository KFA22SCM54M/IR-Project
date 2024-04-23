# Import requests for making HTTP requests
import requests
# Import shutil for high-level file operations
import shutil
# Import os for operating system related tasks
import os
# Import Scrapy for web crawling
import scrapy

# Define a class named WikiCrawler inheriting from scrapy.Spider
class WikiCrawler(scrapy.Spider):

    # Define spider name
    name = "crawler"

    # Define allowed domains for the spider
    allowed_domains = ['en.wikipedia.org']

    # Define the start URLs for the spider
    start_urls = ['https://en.wikipedia.org/wiki/One_Piece']  

    # Define the parse method to handle the response
    def parse(self, response):

        # Initialize a list to store HTML file objects
        html_files = [] 

        # Make a GET request to the seed URL
        seed_content = requests.get('https://en.wikipedia.org/wiki/One_Piece')

        # Write the content of the seed webpage to a file named "One_Piece.html"
        with open("One_Piece.html", 'wb') as f:
            # Write the content to the file
            (f.write(seed_content.content))
		 # Append the file object to the list
            html_files.append(f)

        # Close the file
        f.close()

        # Extract relative links and corresponding titles from paragraph tags (p) in the response
        rel_p_links = [(href,title) for href,title in zip([href for href in response.css('p a::attr(href)').getall() if "cite_note" not in href], response.css('p a::attr(title)').getall())]

        # Extract relative links and corresponding titles from description list tags (dl) in the response
        rel_dl_links = [(href,title) for href,title in zip([href for href in response.css('dl a::attr(href)').getall() if "cite_note" not in href], response.css('dl a::attr(title)').getall())]  

        # Iterate through the combined list of paragraph and description list links
        for href,title in [*rel_p_links, *rel_dl_links]:
            
            # Make a GET request to the webpage corresponding to the relative link
            webpage_content = requests.get(f"http://en.wikipedia.org{href}")
             
            # Define the filename based on the title
            filename = f'{title}.html'
            with open(filename, 'wb') as f:
                # Write the content to the file
                (f.write(webpage_content.content))

                # Append the file object to the list
                html_files.append(f)

        # Close the file
        f.close()


