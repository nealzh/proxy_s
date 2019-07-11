SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `proxy_s`
--
CREATE DATABASE IF NOT EXISTS `proxy_s` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `proxy_s`;

-- --------------------------------------------------------

--
-- 表的结构 `active_proxy`
--

DROP TABLE IF EXISTS `active_proxy`;
CREATE TABLE IF NOT EXISTS `active_proxy` (
  `num_ip` bigint(12) NOT NULL,
  `p_type` varchar(8) NOT NULL,
  `port` varchar(8) NOT NULL,
  `ip` varchar(16) NOT NULL,
  `resp_time` double NOT NULL DEFAULT '0',
  `speed` double NOT NULL DEFAULT '0',
  `valid_times` int(6) NOT NULL DEFAULT '0',
  `invalid_times` int(6) NOT NULL DEFAULT '0',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `add_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `unique_numip_type_port` (`num_ip`,`p_type`,`port`) USING BTREE,
  KEY `is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
