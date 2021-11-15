--Creates the database (SecurityData) and tables needed for storing our queries from AlphaVantage
CREATE DATABASE /*!32312 IF NOT EXISTS*/`SecurityData` /*!40100 DEFAULT CHARACTER SET latin1 */;
--Drop tables incase they exist already
DROP TABLE IF EXISTS SecQueryInfo;
DROP TABLE IF EXISTS SecPriceInfo;

CREATE TABLE secQueryInfo
	(
	--unsigned mediumint used since it saves a byte and auto_increment can't be negative
	`queryID` MEDIUMINT UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
	`symbol` VARCHAR(10) NOT NULL,
	`queryInfo` VARCHAR(100) NOT NULL,
	-- TIMESTAMP used since it saves a byte vs datetime. Need to set the database to EST to be inline with API calls
	`lastQueried` TIMESTAMP NOT NULL
	);
	
CREATE TABLE secPriceInfo
	(
	-- same reasoning as above for mediumint unsigned
	`priceInfoID` MEDIUMINT UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,
	`queryID` MEDIUMINT UNSIGNED REFERENCES SecQueryInfo(queryID)
	`infoTime` TIMESTAMP NOT NULL,
	-- 10,4 floats used since it fits the VAST majority of stock prices. sub $1 generally go out 4 digits
	`open` FLOAT(10,4),
	`high` FLOAT(10,4),
	`low` FLOAT(10,4),
	`close` FLOAT(10,4),
	-- unsigned int used because vol can top out very high depending on the price and activity of the stock and won't be negative
	`vol` INT UNSIGNED
	);