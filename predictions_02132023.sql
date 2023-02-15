-- MySQL dump 10.13  Distrib 8.0.31, for Linux (x86_64)
--
-- Host: localhost    Database: predictions
-- ------------------------------------------------------
-- Server version	8.0.31

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `raw_predictions`
--

DROP TABLE IF EXISTS `raw_predictions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `raw_predictions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` varchar(20) DEFAULT NULL,
  `date` varchar(100) DEFAULT NULL,
  `task_description` varchar(200) DEFAULT NULL,
  `task_category` varchar(50) DEFAULT NULL,
  `unit_of_measure` varchar(30) DEFAULT NULL,
  `pred_low_50_conf` float DEFAULT NULL,
  `pred_high_50_conf` float DEFAULT NULL,
  `pred_low_90_conf` float DEFAULT NULL,
  `pred_high_90_conf` float DEFAULT NULL,
  `actual_outcome` float DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=58 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `raw_predictions`
--

LOCK TABLES `raw_predictions` WRITE;
/*!40000 ALTER TABLE `raw_predictions` DISABLE KEYS */;
INSERT INTO `raw_predictions` VALUES (3,'411347820','10/01/2023','How much bread will I consume during dinner?','food','items',4,6,1,9,3),(4,'411347820','10/01/2023','How long will I test it?','work','minutes',50,90,15,180,700),(5,'411347820','22/01/2023','I will finish this project in 5 days.','work','days',3,6,2,14,4),(6,'411347820','19/01/2023','I will be able to put in 6 hours in the project.','work','hours',3,7,2,12,11),(7,'411347820','18/01/2023','Liza will get up in 90 minutes','work','minutes',40,60,10,140,100),(8,'411347820','19/01/2023','Liza will wake up in 70 minutes','work','minutes',30,50,5,120,80),(9,'411347820','18/01/2023','I will spend on work 2 hours this week.','work','hours',1,3,0,6,2),(10,'411347820','23/01/2023','How many times I will poo this week?','leisure','times',1,2,0,8,2),(11,'411347820','22/01/2023','I will walk for 20 km in this week.','leisure','km',10,15,2,45,11),(12,'411347820','22/01/2023','I will spend 10 hours on my work this week.','work','hours',8,12,2,20,7),(13,'411347820','19/01/2023','We\'ll sell 30 000 boxes this week.','work','units',29000,33000,18000,48000,30926),(14,'411347820','18/01/2023','I will get up 1 minute after my alarm clock will go off.','leisure','mins',4,15,0,15,7),(15,'411347820','01/02/2023','The roses will wilt completely in 3 days!','leisure','days',7,15,7,9,14),(16,'411347820','19/01/2023','I will talk to my parents today for 25 minutes.','leisure','mins',18,30,0,55,23.15),(17,'411347820','19/01/2023','I will deal with pagination in 30 minutes.','work','minutes',25,50,5,180,240),(18,'411347820','19/01/2023','We will have lunch in 60 minutes.','leisure','minutes',40,80,20,110,100),(20,'411347820','18/01/2023','We will return to Russia in 4 month time according to Liza\'s mum.','leisure','months',3,5,1,120,NULL),(24,'411347820','22/01/2023','I\'ll be able to put in 5 hours today on my project.','work','hours',9,14,4,10,6),(25,'411347820','22/01/2023','Our clothes will be dry in 48 hours.','leisure','hours',24,36,6,72,36),(28,'411347820','21/01/2023','Liza will wake up in 30 min','leisure','mins',25,80,2,90,3),(29,'297765243','21/01/2023','Hotel?','byt','hours',11.5,12.5,11.25,13,NULL),(31,'297765243','22/01/2023','when i fall asleed?','byt','hours',11,13,9.5,5,4),(32,'309469492','21/01/2023','Когда доставят еду из Рататуя','доставка','время',20.75,21.5,20.5,22,22.25),(33,'345324164','21/01/2023','At what time I\'ll come into cinema','casual','minutes',7,25,12,17,NULL),(34,'411347820','23/01/2023','I will be able to read for 3 hours today.','leisure','hours',1,4,0.5,9,6),(35,'297765243','22/01/2023','Сколько сегодня я буду ботать нейросети','study','hours',0.25,1,0.1,2,NULL),(36,'411347820','29/01/2023','Number of users I will have by the end of the week','work','person',10,20,8,55,3),(37,'411347820','24/01/2023','Number of new users I will get today?','work','person',2,4,2,10,3),(39,'411347820','25/01/2023','Tomorrow I will spend 3 hours on my work','work','hours',2,3.5,0.5,5.5,1.5),(40,'411347820','01/02/2023','We will eat the soup completely in 5 days','leisure','days',4,6,4,7,6),(41,'411347820','30/01/2023','We will plan your next cycle today in 2 hours','work','hours',1,2.5,0.15,36,3.6),(42,'411347820','29/01/2023','We will solve 2 tests by the end of the day','work','items',1,2,0,20,8),(43,'445089544','01/02/2023','Wait of the average blue whale','zoology','tons',25,150,10,100,NULL),(44,'411347820','02/02/2023','We will finish the current project in 3 days','work','days',3,5,1,9,1),(45,'411347820','05/02/2023','Number of iterations we will need to finish our project','work','int',0,1,0,3,5),(46,'411347820','04/02/2023','Лизе хватит новой банки кофе на дней','еда','дни',21,28,10,50,NULL),(47,'411347820','06/02/2023','Number of hours I will put into 2 version of my bot','work','hours',15,45,5,90,NULL),(48,'411347820','08/02/2023','I will finish cartons calculations in what amount of hours?','work','hours',3,6,1,12,3),(50,'5932724780','11/02/2023','Мы пообедаем чере 120 минут','отдых','мин',55,240,44,180,150),(51,'5932724780','11/02/2023','Я буду готов презентовать вторую версию бота через 3 дня','отдых','дни',0.5,4.5,0.3,5.5,NULL),(52,'5932724780','11/02/2023','Мы приготовим вареники через 2 часа','еда','час',1.5,2.5,1,3.5,NULL),(53,'411347820','11/02/2023','Я опубликую вторую версию бота через 2 дня','работа','дни',2,6,1,6,NULL),(54,'411347820','12/02/2023','Гости опоздают на 5 минут в среднем','leisure','мин',3,10,1,20,NULL),(55,'1043693062','12/02/2023','Аришка самостоятельно сделает шаг в 9 месяцев','Дочь','Месяц',8,12,9,10,NULL),(56,'1043693062','12/02/2023','Война закончится в 2024 году','СВО','Год',2023,2026,2024,2024,NULL),(57,'5118502266','12/02/2023','Война между Украиной и Россией закончится   октябре 2024года','Мир','7',60,60,50,50,NULL);
/*!40000 ALTER TABLE `raw_predictions` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-02-13 20:31:10
