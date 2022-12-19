create table employeaudit(sno int,name_ text,age int,city text,country text,salary int)
create trigger upd_trg before update on employeenew
for each row execute procedure update_table();

create or replace function update_table() returns trigger language PLPGSQL as 
$$
begin 
 if new.name_ <> old.name_ then
		 insert into employeaudit(sno,name_,age,city,country,salary)
		 values(old.sno,old.name_,old.age,old.city,old.country,old.salary);
	end if;
	return new;
end;
$$

select * from employeenew;

update employeenew set
name_= 'Deepash' where sno=6;

select * from employeaudit;
